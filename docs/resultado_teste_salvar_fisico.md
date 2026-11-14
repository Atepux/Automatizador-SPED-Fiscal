# Teste do botão Salvar por clique físico — 13/11/2026

Resultado: interrompido antes de qualquer clique por falta de alvo inequívoco.
O critério completo desta prova não foi alcançado nem testado até a modal.

## Verificações executadas

- Janela principal do PVA encontrada: PID 14432, HWND 1510638.
- Windows não sinalizou a janela como travada (IsHungAppWindow false).
- Nenhuma janela SunAwtDialog/#32770 visível do PVA no início.
- Processo A PID 15848 conectou pelo pyjab à janela principal.
- A etapa de primeiro plano terminou normalmente, sem envio de teclas.
- A busca por push button visível com nome ou descrição Salvar terminou sem
  erro de leitura, mas não produziu exatamente um alvo. A condição de guarda
  salvar_nao_univoco interrompeu a execução em testar_salvar_fisico.py, linha 69
  da versão executada. A contagem exata não foi persistida nesta execução;
  não distinguir ausência de ambiguidade sem nova observação.
- Nenhum clique foi tentado (cliques_tentados=0). O processo B não foi iniciado.
- A liberou suas referências e executou detach, encerrando normalmente.
- Não houve bloqueio nem encerramento forçado de processo.

## Tempos medidos

| Operação | Duração |
| --- | ---: |
| Preparação do primeiro plano | 0,001574 s |
| Busca do botão Salvar | 0,119085 s |
| Supervisor completo até a interrupção | 0,9349 s |

Os timestamps UTC de todas as etapas estão no arquivo A.eventos.jsonl.
O campo do diálogo não foi lido porque nenhum diálogo novo foi aberto.

## Conclusão e continuação

Não é possível concluir nesta execução se click(simulate=True) evita o problema
modal, pois esse método não chegou a ser chamado. Também não houve avaliação
de isJavaWindow/contexto em B. Não houve tentativa alternativa, abertura ou
troca de relatório para fazer aparecer o botão.

Para um próximo teste, o visualizador do relatório pretendido precisa estar
com Salvar disponível. A busca deve confirmar um único botão visível e
habilitado; então recalcular os limites Java, executar um clique físico único
e testar B somente de leitura. Não repetir automaticamente esta execução.
Foi acrescentado registro de contagem antes da guarda para diagnósticos futuros,
sem nova execução de interface nesta etapa.

Nenhum campo foi preenchido, PDF gerado, empresa/competência trocada ou comando
de escrituração executado. Nenhuma chamada doAccessibleActions foi usada para
abrir Salvar. Configuração de acessibilidade preservada.

Script: scripts/testar_salvar_fisico.py, reutilizando preparar_salvar_fisico.py
e o worker B somente de leitura de modal_concorrente.py. Supervisor com prazo
de 25 s para A e 20 s para B, sem kill automático de A; não houve timeout.
Evidências: logs/salvar_fisico_20261113_114443/resultado.json,
A.resultado.json e A.eventos.jsonl. Scripts compilados sem erro sintático.
