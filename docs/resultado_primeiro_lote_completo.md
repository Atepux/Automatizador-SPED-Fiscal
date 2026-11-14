# Primeiro lote completo — 13/11/2026, 15:05

Resultado parcial: quatro PDFs gerados; sequência interrompida no Recibo.
Tempo total: 35,6379 segundos. Não houve continuação após o erro.

Pasta: saida/TESTE_LOTE_COMPLETO_20261113_150504.
Nomes oficiais do cadastro preservados literalmente.

| Relatório | Status | Bytes | Páginas |
| --- | --- | ---: | ---: |
| Operações Próprias | Gerado e validado | 18.624 | 3 |
| Operações ST | Gerado e validado | 23.342 | 3 |
| Documentos de entradas | Gerado e validado | 28.688 | 3 |
| Operações com instrumentos de Pagamentos Eletrônicos | Gerado e validado | 6.982 | 1 |
| Recibo | Erro antes de exportar; nenhum PDF | — | — |
| CIAP | Não executado após interrupção | — | — |
| Documentos de saídas | Não executado após interrupção | — | — |
| Registro de Controle de Créditos Fiscais (opcional) | Não verificado após interrupção | — | — |

Os quatro PDFs abriram com PyMuPDF, sem senha/reparo, todas as páginas
carregadas. Marcadores informativos também foram encontrados nos quatro.
A aprovação do lote atual depende da estrutura, conforme autorização; os
marcadores dos itens novos não foram usados como condição redundante de geração.

Nos dois relatórios de apuração, checkbox confirmada true e Salvar disponível
antes de exportar; sem requisito adicional de estabilidade/conteúdo. Nos demais,
nenhuma ação na opção. Foram usados caminhos hierárquicos e expansão por estado,
cliques físicos dinâmicos para relatório/abertura de Salvar e processos separados.
Diálogo fechado entre os itens. Nenhum retry, sobrescrita ou DIFAL.

## Interrupção

O caminho Escrituração Fiscal → Recibo de Transmissão foi localizado e recebeu
um único clique dinâmico. O worker retornou normally com selected e Salvar
visível, mas Salvar já estava disponível antes: isso não comprova isoladamente
que o visualizador exibiu o recibo. O supervisor gerou RuntimeError entre esse
retorno e o lançamento do processo abrir_salvar, na etapa de verificação do
estado/janelas do PVA. Não houve abertura de Salvar ou PDF do Recibo.

O registro antigo dessa exceção persiste somente seu tipo, não a mensagem,
pilha ou HWND adicional; não é possível identificar retrospectivamente a janela
ou diferença que causou a recusa. Uma inspeção Win32 posterior somente de leitura
encontrou apenas a janela principal, PID 30852/HWND 592210. Não foi fechado
qualquer diálogo, repetido clique ou tentada técnica alternativa.

O PVA usado foi o que estava aberto no início deste lote, PID 30852, e esse
PID permaneceu constante durante a execução. Nenhuma troca de empresa ou
competência foi realizada pela automação. Nenhuma biblioteca instalada, dado
fiscal registrado ou operação de escrituração executada. A opção de ignorar
ausência do relatório opcional não foi exercitada porque o lote parou antes.

## Código e registros

scripts/lote_cadastro_atual.py limita esta autorização aos oito IDs cadastrados,
com pasta exclusiva e trava persistente. Reutiliza o fluxo aprovado e para em
erro real. Navegação agora distingue CaminhoAusente de ambiguidade/erro Java:
somente ausência sem clique de um item opcional pode ser ignorada. O Recibo
é obrigatório e por isso sua falha interrompeu a sequência.

Evidências: logs/lote_completo_20261113_150504/resultado.json e subpastas
01_operacoes_proprias a 05_recibo. Script compilado antes da execução.
Não avançou para outras empresas. Não repetir o lote ou arquivos já criados
sem nova autorização e proteção contra sobrescrita.
