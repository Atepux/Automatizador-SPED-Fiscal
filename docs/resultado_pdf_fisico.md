# Conclusão do salvamento físico — 13/11/2026, 11:48

Critério atendido: relatorio_teste_fisico.pdf criado e estruturalmente válido.

Foi usada exclusivamente a janela Salvar já aberta pelo clique físico do
teste anterior: HWND 1249104, SunAwtDialog, título Salvar, pertencente ao PVA
PID 14432. Nenhuma janela de relatório ou salvamento foi reaberta nesta etapa.

A conexão seguiu a estratégia bem-sucedida de Service/load_library,
assinaturas ctypes, Windows_run, fila inicial de mensagens, isJavaWindow e
getAccessibleContextFromHWND. Reconhecimento e contexto retornaram true.

Campo Nome do arquivo e botão Salvar identificados univocamente por nome/papel,
com estados habilitado/editável/visível conferidos. A pasta de testes foi
assegurada e o destino conferido inexistente antes de preencher e imediatamente
antes da confirmação. Caminho absoluto confirmado integralmente por leitura.

Destino: saida/TESTE_FICTICIO/relatorio_teste_fisico.pdf, sob a pasta do projeto.
Botão de confirmação acionado uma única vez, sem repetição. Não houve janela
inesperada. Diálogo fechou e tamanho/data do arquivo estabilizaram.

## Verificação e tempos

- Tamanho: 3.539 bytes.
- Páginas: 1.
- PyMuPDF: arquivo PDF aberto, sem senha e sem reparo; página carregada.
- Worker PID 29548 encerrou normalmente, exit code 0, sem timeout.
- Configuração de acessibilidade preservada.

| Etapa | Duração |
| --- | ---: |
| Reconhecimento Java | 0,005119 s |
| Obtenção de contexto | 0,001502 s |
| Localização de campo/botão | 0,158278 s |
| Preenchimento | 0,002363 s |
| Confirmação por leitura | 0,005616 s |
| Ação de confirmação Salvar | 0,185029 s |
| Espera por gravação estável | 1,263009 s |
| Verificação PyMuPDF | 0,041859 s |
| Supervisor completo | 3,378200 s |

A fila inicial de mensagens levou 1,022744 s. Todos os timestamps e demais
tempos estão no JSONL. Supervisor com timeout externo de 35 s; não atingido.
Trava persistente impede repetir essa autorização; arquivo existente também
impede sobrescrita. Nenhum conteúdo fiscal foi extraído ou registrado.

Esta conferência é estrutural, não uma validação fiscal ou visual do relatório.
Nenhuma empresa, competência ou relatório foi alterado. Nenhuma biblioteca
instalada e nenhum outro PDF gerado. Abertura física e conclusão do salvamento
foram comprovadas em etapas separadas; execução contínua de ponta a ponta
ainda não foi testada com essa nova estratégia. Não há execução em lote.

Script: scripts/concluir_pdf_fisico.py.
Evidências: logs/concluir_fisico_20261113_114856/resultado.json,
worker.resultado.json e worker.eventos.jsonl.
