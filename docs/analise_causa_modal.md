# Análise da janela modal — 13/11/2026

## Conclusão

A hipótese principal é uma interação de sincronização/ciclo de vida entre a
ação acessível que abre a modal e o cliente da Java Access Bridge que a iniciou.
O encerramento de A antes da conexão de B é um fator de confusão relevante.
Não foi comprovada uma causa única; separar processos e matar A não foi uma
correção validada. PID ou classe Windows incorretos não são a explicação mais
provável com as evidências existentes.

Esta etapa fez somente revisão de código/logs, consulta documental e uma
enumeração Win32 de leitura. Nenhum script de fluxo, conexão Java nova,
clique, mudança de campo ou salvamento foi executado. Na consulta atual,
o PVA estava no PID 14432/ HWND principal 1510638, sem diálogo visível.

## Comparação dos testes

| Característica | Isolado bem-sucedido | Completo com workers |
| --- | --- | --- |
| Abertura do diálogo | Manual, anterior ao Python | Ação Java de A no botão Salvar |
| PID do PVA | 14432 | 14432 |
| HWND do diálogo | 658798 | 1117520 |
| Título identificado | Salvar | Salvar |
| Classe | SunAwtDialog | SunAwtDialog |
| Primeira conexão ao diálogo | JABDriver(hwnd=..., timeout=5) | Mesma estratégia, mesmo timeout |
| DLL cliente configurada | Java 8u511, WindowsAccessBridge-32.dll | Mesma DLL |
| Python/Java | Python 3.14 32 bits / Java privado 21 64 bits | Mesma configuração |
| Estado do cliente que abriu a modal | Nenhum cliente Python abridor | A encerrado à força antes de B |
| Resultado | Contexto utilizável; campo lido e preenchido; PDF salvo | RuntimeError na conexão; depois TimeoutError aguardando título |

Os HWNDs diferirem é esperado em janelas criadas em momentos distintos; não
devem ser reutilizados como identificadores persistentes. O título e a classe
confirmam a janela Windows, mas não garantem contexto Java válido.

Nos testes antigos, VMID/contexto Java do diálogo não foram persistidos. No
isolado houve contexto operacional, comprovado pelas leituras e escrita.
No completo não houve contexto utilizável demonstrado por B. Não é possível
comparar numericamente VMID/contextos nem provar sua invalidação. Referências
Java não devem ser transmitidas entre processos como handles reutilizáveis.

## Estratégia de conexão e falha

scripts/salvar_pdf_unico.py usou JABDriver com HWND explícito. O primeiro B fez
o mesmo. Portanto, trocar apenas a busca por título não explica nem resolve
a diferença entre esses dois casos.

O HWND explícito ignora a espera por descoberta da janela; a inicialização
local chama Windows_run, bombeamento de mensagens e obtenção de contexto.
A primeira falha de B foi registrada somente como RuntimeError, sem pilha ou
retorno individual das funções gateway. Não atribuir essa falha específica
com certeza a isJavaWindow ou getAccessibleContextFromHWND.

A continuação usou JABDriver(title='Salvar', timeout=8), que enumera títulos
e exige isJavaWindow. Terminou em wait_java_window_by_title com TimeoutError.
Isso comprova falha da descoberta Java naquele processo; não comprova que
o diálogo estivesse ausente do Windows nem qual etapa do registro falhou.
Não há registro individual dos retornos de isJavaWindow nesse teste.

## Sincronismo e encerramento

No pyjab instalado, _do_accessible_action chama doAccessibleActions diretamente,
sem lançar uma tarefa assíncrona própria. No código público do OpenJDK 21u,
essa ação é encaminhada por invokeAndWait ao AccessibleAction do componente.
Em Java, exibir um Dialog modal pode manter setVisible(true) pendente até o
fechamento, com processamento de eventos em laço modal. Essa combinação torna
plausível uma chamada pendente/reentrância na bridge, mas não prova o stack
real do PVA ou da DLL instalada.

Os eventos do teste mostram antes_abrir_salvar às 14:10:43.730 UTC e
depois_abrir_salvar às 14:10:51.741 UTC: cerca de 8,011 s. O diálogo continuava
aberto depois. Portanto, a afirmação de que a chamada Python ficou bloqueada
durante toda a vida da modal seria incorreta. Falta determinar se o retorno
correspondeu à conclusão Java ou a um limite/retorno intermediário do transporte.

Após esse retorno, o código chamou os._exit(0), sem nova conexão ou pump.
A ainda não havia terminado ao completar 40 segundos de execução e foi morto
pelo supervisor. Somente então B começou. O código público da bridge Windows
tem limpeza em DLL_PROCESS_DETACH e envio síncrono de AB_DLL_GOING_AWAY às JVMs.
Isso oferece um mecanismo plausível para espera no encerramento quando há
uma ação modal em curso. Não houve pilha nativa que comprove esse mecanismo
na DLL Java 8u511 usada aqui. Matar A pode ter interferido no registro de B,
mas não deve ser tratado como fato causal comprovado.

Outras hipóteses: registro assíncrono não concluído, fila de mensagens não
atendida e particularidade da combinação DLL Java 8/VM Java 21. Essa combinação
funcionou no teste isolado e na janela principal; não é justificativa suficiente
para instalar ou trocar runtimes sem evidências adicionais.

## Proposta de correção, não implementada

Prioridade: substituir a sequência serial abrir → encerrar A → iniciar B por
coordenação concorrente, sem encerrar o cliente abridor durante a modal.

1. Supervisor sem bridge identifica o PVA e verifica ausência de diálogos.
2. A mantém o cliente Java vivo, localiza o botão e registra a tentativa única.
3. Supervisor observa a abertura pelo Win32 sem depender de a chamada de A
   retornar; inicia B enquanto A permanece ativo.
4. B inicializa sua própria bridge e valida PID/HWND/título/classe. Registra
   separadamente isJavaWindow e sucesso de getAccessibleContextFromHWND,
   VMID e validade do contexto, sem dados do relatório.
5. O primeiro teste dessa arquitetura deve somente conectar/inspecionar,
   sem salvar. Se A tiver retornado, mantém a fila da thread bridge atendida;
   se estiver em chamada nativa, o supervisor não exige que ela retorne para B.
6. Timeout sinaliza falha e preserva os estados. Não matar A automaticamente
   e seguir tentando B sob a mesma modal. A política de recuperação precisa
   prever interrupção sem novos cliques e sem fechar o PVA.

Esse experimento distingue problema causado pelo encerramento de A de uma
limitação da própria ação acessível modal. Se B continuar sem acesso com A
vivo, outra proposta é abrir Salvar por um único clique físico calculado do
botão Java, evitando a ativação síncrona AccessibleAction. É uma hipótese para
teste futuro, não uma técnica executada nesta etapa. Ambas exigem autorização
de teste; não há nova implementação ou salvamento nesta análise.

## Alternativa nativa Windows

pywin32 já comprovou enumeração da janela superior. Isso não prova acesso ao
campo como Edit nativo: SunAwtDialog/Swing pode expor apenas a janela superior
ao Win32, com controles internos desenhados em Java. EnumChildWindows deve
confirmar controles/IDs reais antes de cogitar WM_SETTEXT ou mensagens de botão.
Não usar o HWND superior como se fosse o campo Nome do arquivo.

UI Automation é alternativa condicionada à exposição efetiva do campo/botão
e de padrões de edição/ativação. Não é garantida pela aparência do diálogo.
Não é obrigatório instalar pywinauto para uma inspeção UIA: uma API COM do
Windows pode ser avaliada com ferramentas disponíveis, caso autorizado.
Nesta etapa não havia diálogo aberto para verificar os controles internos,
e não foi iniciado novo teste. pywinauto continua não instalado.

## Fontes e evidências

- logs/salvamento_unico_20261113_103205.json e campo_salvar_20261113_102815.json.
- logs/completo_isolado_20261113_110949/A.eventos.jsonl, B.eventos.jsonl e
  resultado_anterior.json; scripts correspondentes e pyjab instalado.
- [OpenJDK 21u: AccessBridge.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/jdk.accessibility/windows/classes/com/sun/java/accessibility/internal/AccessBridge.java), método doAccessibleActions.
- [Java 21: Dialog.setVisible](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Dialog.html#setVisible(boolean)).
- [OpenJDK 8u: WinAccessBridge.cpp](https://raw.githubusercontent.com/openjdk/jdk8u/master/jdk/src/windows/native/sun/bridge/WinAccessBridge.cpp), DllMain/destrutor. Código de referência, não dump da DLL instalada.
- [Oracle: gateway da Java Access Bridge](https://docs.oracle.com/en/java/javase/21/access/java-access-bridge-api.html).
- [Microsoft: EnumChildWindows](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumchildwindows).
- [Microsoft: padrões UI Automation](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-controlpatternsoverview).
