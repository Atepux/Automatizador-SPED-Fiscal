# Investigação de processos separados — 13/11/2026

## Instrumentação e revisão

O script scripts/investigar_modal.py implementa supervisor e workers isolados.
Cada chamada instrumentada grava eventos antes/depois com timestamp UTC e PID,
usando flush e fsync imediatos. Instrumenta conexão, inicialização da bridge,
Windows_run, bombeamento de mensagens, obtenção de contexto por HWND, inspeção,
seleção, abertura do diálogo e preenchimento. Não confirma salvamento.

O supervisor aplica timeout externo de 30 segundos por worker e encerra somente
o processo filho que criou. Um dump de stack é agendado para 12 segundos, sem
variáveis locais. O timeout do próprio JABDriver não é usado como garantia
contra bloqueios nativos. Não há repetição automática de clique.

Na revisão do fluxo anterior, após abrir Salvar existem chamadas a
driver._pump_messages(), enumeração de janelas, criação de segundo JABDriver e
inspeção do diálogo. A criação do driver chama Service/load_library,
Windows_run, _pump_messages, getAccessibleContextFromHWND, isJavaWindow e
criação do elemento raiz. Como não havia eventos antes/depois dessas chamadas,
o registro histórico não identifica a chamada exata que bloqueou.

## Execução observada

A janela Salvar não estava aberta nesta investigação. A verificação inicial
interrompeu antes de qualquer interação. Uma consulta de leitura confirmou
somente a janela principal do PVA, PID 14432.

Foi então executado o Processo A autorizado, PID 22976:

- Conexão com a janela principal retornou normalmente.
- Localização do caminho de Operações Próprias foi concluída.
- Uma chamada addAccessibleSelectionFromContext retornou; selected foi confirmado.
- A espera de carregamento terminou normalmente.
- A busca pelo botão Salvar terminou, mas não encontrou controle utilizável.
- O worker encerrou com RuntimeError de forma controlada, sem timeout.
- Não houve clique para abrir Salvar. Não houve chamada de confirmação de PDF.

Uma inspeção adicional independente e somente de leitura encontrou zero botões
com descrição acessível Salvar. A causa da diferença do visualizador em relação
ao teste anterior não foi determinada; não foi acionado outro comando para
contornar essa condição.

O supervisor não executou B porque a janela Salvar estava ausente. O marcador
janelas_mudaram do resumo inclui essa ausência; não significa que tenha surgido
outra janela. A verificação de preservação da configuração de acessibilidade
retornou true. Nenhum arquivo de teste foi criado e o PVA não foi encerrado.

## Conclusão e continuação

Não houve bloqueio nesta execução. Nenhuma chamada exata do bloqueio anterior
pode ser atribuída com segurança. Também não é possível concluir que a janela
modal foi a causa, nem que processos separados resolveram o problema: o teste
de B ficou pendente por falta do diálogo.

Para continuar, disponibilizar manualmente a janela Salvar do mesmo relatório.
O supervisor poderá dispensar A e testar B diretamente com limite externo,
preenchendo apenas o caminho fictício teste_processos_separados.pdf. O modo
probe é somente de leitura e investiga conexão da principal sob modal antes
da conexão ao diálogo; não reproduz integralmente o histórico em que a primeira
conexão ocorreu antes da abertura da modal.

Arquitetura recomendada provisoriamente: supervisor sem bridge e workers de
vida curta por etapa, comunicando apenas PID/HWND e resultados técnicos, com
timeout externo e nenhuma repetição automática de ações de interface. Separar
workers é uma medida de contenção de bloqueios; sua eficácia para este fluxo
ainda precisa ser comprovada com o diálogo disponível.

Evidência: logs/modal_20261113_105258/resultado.json e A.jsonl.
Não houve troca de empresa, competência ou relatório diferente de Operações
Próprias. Não houve instalação de bibliotecas, salvamento ou acesso externo.
