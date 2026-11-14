# Seleção única — 13/11/2026

Critérios recebidos explicitamente do usuário, mantidos apenas em memória e no
canal de entrada do processo auxiliar. Nenhum CNPJ, período, nome empresarial,
Inscrição Estadual ou conteúdo de registros foi persistido nos logs.

## Implementação

`scripts/selecao_escrituracao.py` resolve as colunas pelo cabeçalho Java,
compara CNPJ e datas e exige correspondência única. Inscrição Estadual,
Finalidade do Arquivo e Estado podem restringir a busca. O Estado informado
pelo usuário foi exigido neste teste. Não se escolhe a primeira linha.

A seleção utiliza `table.select_row()`. A confirmação exige `selected_rows`
com exatamente o índice encontrado, `is_row_selected()` verdadeiro e nova
leitura dos critérios na linha selecionada. Se a linha correta já estiver
selecionada, não ocorre nova seleção. O botão Ok é acionado uma única vez por
clique físico com limites Java dinâmicos, após conferir foco e estado.

Processo auxiliar isolado, timeout externo de 55 segundos e logs imediatos por
chamada crítica. Somente o auxiliar criado pode ser encerrado no timeout.
Exceções de bibliotecas não têm suas mensagens gravadas para evitar exposição
de dados. A entrada padrão é usada para não salvar os critérios em arquivos
nem passá-los como argumentos ao processo auxiliar.

A confirmação posterior está preparada de forma conservadora: mesmo controle
visível contendo CNPJ e ambas as datas, ou título principal com esses dados.
Não reúne textos independentes para inferir identidade. Esse critério ainda
não foi validado na interface efetivamente aberta e pode exigir mapeamento.
O diagnóstico inicial continua sendo a entrada padrão da V2; a nova seleção
nunca é chamada automaticamente por ele.

## Resultado observado

- Leitura inicial: correspondência única, inclusive Estado.
- Primeiro processo de seleção: linha Java selecionada e conferida; Windows
  recusou SetForegroundWindow. Nenhum clique em Ok ocorreu nessa execução.
- Continuação com tratamento de foco já usado pelo projeto: preservou a
  seleção correta, sem selecioná-la novamente; exatamente um clique em Ok.
- Cerca de 0,1 segundo após o clique, a enumeração Windows retornou uma janela
  de diálogo diferente da janela de seleção. O fluxo interrompeu imediatamente,
  sem confirmar, fechar ou interagir com a janela apresentada.
- A primeira implementação não persistiu a janela divergente antes de parar;
  portanto não é possível afirmar seu título, tipo específico ou finalidade.
  Foi acrescentado esse registro sanitizado para uma futura execução autorizada.
- Uma consulta posterior somente de leitura Windows encontrou apenas a janela
  principal SunAwtFrame, sem diálogos visíveis. Isso sugere comportamento
  transitório, mas não comprova abertura da escrituração correta.
- Identidade ativa não confirmada. Prova de abertura ainda **não aprovada**.

Não ocorreram novos cliques, abertura de outros registros, fechamento de
escrituração, geração de relatórios ou PDFs após a interrupção. Nenhuma ação
de validação, alteração ou transmissão foi executada. A V1 não foi modificada.

## Testes offline

Nove testes passaram: dois de privacidade e sete de seleção, incluindo
ausência/duplicidade, período divergente, desambiguação, Estado e validação
de entrada. Esses testes não comprovam o comportamento de abertura no PVA.

## Evidências

- `logs/selecao_unica_20261113_155219`: leitura, sem seleção.
- `logs/selecao_unica_20261113_155232`: seleção confirmada, zero cliques Ok.
- `logs/selecao_unica_20261113_155306`: um clique Ok e interrupção; enumeração
  Windows posterior em `janelas_apos_interrupcao.json`.

Próxima investigação requer autorização: identificar somente a informação
de identidade na janela principal já existente, sem nova abertura, e mapear
o diálogo transitório antes de autorizar seu tratamento no fluxo.
