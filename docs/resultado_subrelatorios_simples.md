# Regra simplificada aprovada — 13/11/2026, 12:31

8 testes offline passaram: checkbox já marcada não recebe ação; desmarcada
recebe uma ação e exige confirmação; falha de leitura, ação, timeout ou
checkbox/Salvar não confirmados interrompem. Evidência de estabilidade e
atualização foi removida dos requisitos e do fluxo de subrelatórios.

Execução autorizada somente de dois relatórios, na mesma empresa/competência,
sem intervenção manual. Expansão automática mantida; pais já expandidos nesta
execução não receberam ação. Nenhum DIFAL ou relatório adicional executado.

| Relatório | Checkbox inicial → final | Ações na caixa | Bytes | Páginas | Tempo |
| --- | --- | ---: | ---: | ---: | ---: |
| Operações Próprias | true → true | 0 | 18.624 | 3 | 7,8040 s |
| Operações ST | false → true | 1 | 23.340 | 3 | 8,0797 s |

Ambos tiveram nova confirmação true antes da exportação; Salvar disponível,
caminho absoluto confirmado por leitura e uma confirmação de salvamento por
arquivo. PDFs abertos/carregados pelo PyMuPDF, sem senha/reparo. Marcadores de
Operações Próprias e Substituição Tributária/Operações ST, com Apuração do ICMS,
confirmados. Diálogo fechado antes de iniciar o próximo. Nenhum timeout, retry
ou sobrescrita; todos os workers terminaram normalmente. Total: 16,0299 s.

Pasta exclusiva: saida/TESTE_SUBRELATORIOS_20261113_123119. Nomes oficiais
preservados literalmente. Evidências: logs/validar_subrelatorios_20261113_123119.
Comparações históricas permanecem informativas e não condicionam a nova regra.
Nenhum texto fiscal registrado. Não houve troca de empresa/competência nem
instalação de bibliotecas. Não houve execução de outros relatórios.

Teste: tests/test_subrelatorios_simples.py. A suíte antiga de estabilidade foi
substituída; o motor experimental de estabilidade não é chamado pelo fluxo.
