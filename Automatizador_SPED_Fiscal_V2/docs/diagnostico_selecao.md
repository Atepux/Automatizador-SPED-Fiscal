# V2 — seleção de escriturações: inspeção inicial

13/11/2026, 15:29. Conexão pyjab bem-sucedida com o PVA PID 30852 e janela
principal HWND 592210, classe SunAwtFrame. Lidos 182 controles, sem timeout.
Configuração de acessibilidade preservada. Nenhuma ação de interface executada.

## Controles efetivamente encontrados

| Controle/caminho | Papel Java | Estados relevantes | Ação exposta |
| --- | --- | --- | --- |
| Barra de menus → Escrituração Fiscal | menu | enabled, visible, showing, selectable | clicar |
| Escrituração Fiscal → Abrir | menu item | visible, selectable; sem enabled | clicar |
| Escrituração Fiscal → Fechar | menu item | enabled, visible, selectable | clicar |
| Contribuinte | menu | visible, showing, selectable; sem enabled | clicar |
| Área do relatório → Fechar | push button | enabled, visible, showing | clicar |

Menu Fechar e botão Fechar do relatório são controles distintos; um futuro
fluxo não deve escolher só pelo nome global. Também existem itens de importação,
edição, exclusão e transmissão: não foram acionados e não integram a proposta
de navegação autorizada. Os índices do diagnóstico são evidência desta sessão,
não seletores fixos. Localização futura deve usar pai/caminho, papel e nome.

Os filhos dos menus foram expostos pela bridge mesmo com menu fechado. Por
isso foi possível observar Abrir sem clicar no menu. Ausência de enabled indica
indisponibilidade naquele instante; a ação clicar existir não autoriza nem
garante a execução do comando.

## Lista de empresas e competências

Não havia diálogo de seleção aberto. Nenhuma tabela de escriturações foi
observada. Há árvores da área de escrituração e listas do visualizador, que
não devem ser confundidas com a lista de empresas/competências.

Não foram confirmados nesta etapa:

- Título/classe/contexto Java do diálogo de abertura.
- Papel e estrutura da lista, seus cabeçalhos, filtros e botões de confirmação.
- Disponibilidade de CNPJ, início/fim do período, IE, perfil ou tipo na lista.
- Controle que permita reler CNPJ/período da escrituração após abrir.
- Necessidade de fechar a escrituração atual antes de habilitar Abrir.

O menu Abrir desabilitado sugere uma condição de estado — possivelmente a
escrituração atual aberta —, mas a causa não foi comprovada. Não acionar Fechar
para investigar sem autorização. Não existe caminho alternativo inventado.

## Procedimento necessário, ainda não executado

1. Observar as condições que habilitam Escrituração Fiscal → Abrir, mediante
   autorização específica ou preparação manual pelo usuário.
2. Acionar somente esse comando quando habilitado; inspecionar a janela que
   realmente aparece, confirmando mesmo PID/owner/contexto.
3. Identificar cabeçalhos estáticos e como ler uma linha de forma estruturada.
   A próxima inspeção pode registrar nomes de colunas e flags de presença,
   sem nomes de empresas, CNPJs completos, valores ou linhas fiscais nos logs.
4. Confirmar a ação de abrir uma linha e os controles da identidade ativa
   ANTES de implementar seleção automática em série.

Esta etapa parou no passo de observação, conforme a restrição do usuário.

## Proposta de seleção segura

Cadastrar alvos explicitamente, em configuração local protegida e separada
dos logs: CNPJ completo para comparação apenas em memória, período inicial/final
e, se necessário para distinguir duplicatas, IE/perfil/finalidade/identificador
da escrituração. Esses campos são requisitos propostos, não colunas confirmadas.
Não inserir CNPJ real em arquivos-exemplo ou inventar valores.

Resolver cada execução pelo conteúdo dos campos e não por posição/ordem/nome
da empresa. Normalizar CNPJ somente para comparação (14 dígitos), e comparar
datas exatas do período, não apenas um rótulo mensal. Se houver zero ou mais
de uma linha compatível, interromper sem escolher a primeira. Estado selected
não comprova abertura, como já observado na árvore de relatórios.

Depois da abertura, reler CNPJ e intervalo de datas dos controles da identidade
ativa e comparar com o alvo antes de chamar o gerador V1. Sem fonte independente
confirmada dessa identidade, não iniciar PDFs. Se só o nome estiver acessível,
o critério de seleção automática ainda não está atendido.

Logs devem conter alias interno, resultado de igualdade e códigos de erro,
sem CNPJ completo ou hash simples de CNPJ como substituto. Processos distintos
não compartilham referências de objetos Java; adquirir contexto próprio.
Guardar escolha de empresa/competência separada do cadastro de relatórios:
não presumir que todos os relatórios se apliquem a todas as empresas.

## Evidências e preservação

logs/diagnostico_20261113_152900/interface.json e resumo.json. Nomes dinâmicos
foram omitidos por lista permitida; nem screenshots nem valores de campos ou
descendentes de tabelas/listas/árvores foram coletados. Nenhuma biblioteca
instalada. V1 não executada/importada; apenas lida para copiar/hash. Verificação
de preservação em v1_preservacao.json.
