# Fluxo completo com workers isolados — 13/11/2026

Resultado: incompleto. Relatório ativado, Salvar aberto; PDF não criado.
Nenhum sucesso de gravação ou integridade estrutural pode ser declarado.

Destino reservado para esta prova:
saida/TESTE_FICTICIO/teste_fluxo_completo_operacoes.pdf.
O destino não existia e continuou inexistente ao final.

## Procedimento e evidências

Supervisor: scripts/fluxo_completo_isolado.py. Reutiliza o worker de
scripts/ativar_operacoes_proprias.py para abrir o relatório e o diálogo.
Cada worker tem limite externo de 40 segundos; somente o processo filho pode
ser terminado. A abertura do diálogo e a confirmação de salvamento têm contagem
separada e não são repetidas automaticamente. As travas anteriores permanecem.

Preparação inicial interrompida pelo Windows ao solicitar primeiro plano, sem
clique. Seu registro foi preservado em A.preparacao_anterior.json. A continuação
da mesma prova verificou zero cliques anteriores e ausência da trava de ativação.
A correção do foco vinculou temporariamente as filas de entrada e sempre
desfez o vínculo, sem enviar teclas.

Processo A:

- Resolveu por nomes exatos o caminho Escrituração Fiscal → Relatórios de
  Registros Fiscais → Apuração do ICMS → Operações Próprias.
- Confirmou pais expandidos e visibilidade. Restaurou/confirmou primeiro plano.
- Deu um único clique físico com ponto calculado dos limites Java atuais.
- Confirmou selected e Salvar visível/habilitado. Salvar também já estava
  disponível antes desta nova ativação; esta etapa não usa selected sozinho.
- Acionou Salvar uma única vez. A chamada retornou após cerca de 8 segundos.
- Gravou depois_abrir_salvar e solicitou encerramento imediato do worker,
  sem segunda conexão nem bombeamento sob modal. O processo não terminou no
  prazo e foi finalizado pelo supervisor.
- O supervisor confirmou exclusivamente o diálogo esperado Salvar,
  SunAwtDialog, HWND 1117520, pertencente ao PID 14432 do PVA.

Processo B:

- Nova sessão Python identificou o mesmo diálogo pelo Win32.
- A conexão JABDriver com HWND direto gerou RuntimeError antes do preenchimento.
  Não houve clique nem mudança de texto nesse processo.
- Uma continuação limitada à conexão, sem repetir cliques, usou título Salvar
  para aguardar o registro assíncrono da janela na bridge.
- Essa espera terminou em TimeoutError em JABDriver.wait_java_window_by_title
  (jabdriver.py, linha 425 na versão instalada). A pilha técnica foi registrada
  sem mensagens que pudessem conter dados fiscais.

## Tempos observados

| Etapa | Tempo |
| --- | ---: |
| Conexão, localização, foco e preparação de A até o clique | 1,2872 s |
| Clique físico do nó | 0,0383 s |
| Confirmação do visualizador após o clique | 0,3050 s |
| Ação Java de abertura de Salvar | 8,0111 s |
| Worker A até timeout/encerramento externo | 40,0221 s |
| Primeiro worker B, conexão direta interrompida | 0,4039 s |
| Conexão de B aguardando o título, até TimeoutError | 7,5477 s |
| Segundo worker B, incluindo inicialização | 7,8031 s |

Timestamps UTC e durações estão nos eventos JSONL. Os tempos de carregamento
acima são observacionais, não garantias para outros relatórios ou ambientes.
Preenchimento, confirmação de gravação e PyMuPDF não foram alcançados.

## Conclusão técnica

Separar processos conteve a espera indefinida e preservou o PVA, mas não
resolveu o fluxo completo nesta configuração. A conexão de B não reconheceu
como janela Java o diálogo que o Win32 identificou. Não há evidência suficiente
para atribuir isso a incompatibilidade de versão, registro da bridge ou
encerramento do cliente anterior. Não instalar ou trocar runtimes por suposição.

O ponto observado em A é posterior ao retorno da ação de abrir Salvar, na
solicitação de saída do processo. Não foi colhida pilha nativa; não atribuir
com certeza a uma rotina específica de descarregamento de DLL. Em B, a espera
por janela Java e seu timeout estão identificados pela pilha registrada.

Próxima investigação proposta: inspecionar o registro do diálogo pela bridge
mantendo o cliente que abriu a modal vivo e usar um worker independente com
supervisão, ou obter o contexto modal pela bridge já inicializada, sem criar
outro driver. Requer um teste dedicado; nenhuma dessas alternativas foi
executada e nenhum clique deve ser repetido automaticamente.

## Estado final e privacidade

Nenhum PDF foi criado, preenchimento não executado, nenhuma confirmação de
salvamento. A última observação mantém Salvar aberto e o PVA não foi encerrado.
Não houve troca de empresa/competência, outro relatório, instalação ou operação
sobre escriturações. Configuração de acessibilidade preservada. Logs contêm
somente estados, caminhos fictícios, tempos, PIDs/HWNDs e pilha técnica.

Evidências em logs/completo_isolado_20261113_110949/:
A.json, A.eventos.jsonl, B.eventos.jsonl, resultado_anterior.json e resultado.json.
O resumo anterior preserva A e a primeira conexão de B; resultado.json contém
a continuação exclusiva de B. Não executar novamente para repetir cliques.
