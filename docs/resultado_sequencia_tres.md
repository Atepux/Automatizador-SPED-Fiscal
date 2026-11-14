# Sequência de três relatórios aprovada — 13/11/2026, 11:55

Uma execução coordenada gerou os três PDFs autorizados na mesma escrituração,
sem intervenção manual, troca de empresa/competência ou relatórios adicionais.

Pasta exclusiva: saida/TESTE_TRES_RELATORIOS_20261113_115502.
Não foram utilizadas pastas definitivas das empresas. Os nomes abaixo foram
preservados literalmente, sem inclusão automática de competência ou CNPJ.

| Nome exato do PDF | Bytes | Páginas | Duração do relatório | Resultado |
| --- | ---: | ---: | ---: | --- |
| Registros Fiscais da Apuração do ICMS_Operações Próprias.pdf | 3.539 | 1 | 6,4401 s | Aprovado |
| Registros Fiscais da Apuração do ICMS_Operações ST.pdf | 3.527 | 1 | 5,9758 s | Aprovado |
| Registros Fiscais dos documentos de entradas de mercadorias e aquisição de serviços.pdf | 28.688 | 3 | 5,8676 s | Aprovado |

Tempo total da sequência: 18,3267 segundos. Os três PDFs abriram no PyMuPDF,
sem senha ou reparo, e todas as páginas foram carregadas. Marcadores de tipo
de relatório foram identificados no texto processado somente em memória:
Operações Próprias/Apuração do ICMS; Substituição Tributária ou Operações ST/
Apuração do ICMS; identificação de entradas. Logs persistem apenas booleanos,
não o conteúdo fiscal. A conferência de marcadores complementa a integridade
estrutural; não valida valores fiscais ou aparência integral.

## Caminhos usados

Sob Escrituração Fiscal → Relatórios de Registros Fiscais:

- Apuração do ICMS → Operações Próprias.
- Apuração do ICMS → Substituição Tributária, correspondente ao nome solicitado
  Operações ST. Essa diferença de rótulo não alterou o nome do PDF.
- Documentos → Entradas de Mercadorias e Aquisição de Serviços.

## Segurança e coordenação

Reutilizados os workers aprovados do teste ponta a ponta. Cada caminho foi
resolvido por nomes entre filhos imediatos, com pais expandidos. Clique físico
dinâmico tanto na folha quanto no Salvar do visualizador, sem coordenadas fixas
ou ação Java síncrona para abrir a modal. Outro processo obteve contexto Java,
preencheu o caminho absoluto, confirmou por leitura e salvou uma única vez.

Todos os destinos foram conferidos inexistentes. Houve uma confirmação por
PDF, sem sobrescrita ou retry. Arquivos estáveis e fechamento do diálogo foram
confirmados antes de iniciar o próximo relatório. Mesma janela principal/PID
do PVA (14432) em toda a sequência. Nenhuma modal inicial ou janela inesperada.
Todos os workers encerraram normalmente, sem timeout ou kill; configuração de
acessibilidade preservada. Não houve instalação ou operações sobre escriturações.

O supervisor interrompe na primeira falha de PDF, marcadores, worker ou janela;
a autorização desta sequência tem trava persistente. A pasta é criada de forma
exclusiva. Não expandir para outros relatórios/empresas sem nova autorização.

## Projeto e evidências

- config/poc_tres_relatorios.json: caminhos, nomes literais e marcadores desta
  POC; não presume aplicabilidade às outras empresas.
- scripts/poc_tres_relatorios.py: sequência limitada aos três itens.
- scripts/poc_ponta_a_ponta.py: rotina aprovada parametrizada para cada caso;
  exige diálogo fechado e marcadores confirmados nesta sequência.
- logs/sequencia_tres_20261113_115502/resultado.json: resumo individual e geral.
- Subpastas 01_operacoes_proprias, 02_operacoes_st e 03_documentos_entradas:
  resultados, timestamps UTC e duração de cada etapa/worker.

Os scripts foram compilados sem erro sintático antes da execução real.
Nenhuma execução foi iniciada para as demais empresas.
