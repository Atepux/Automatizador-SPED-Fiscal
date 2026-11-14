# Validação de subrelatórios interrompida — 13/11/2026, 12:08

Resultado: sequência interrompida antes do primeiro clique. Nenhum PDF criado.
O critério de sucesso não foi alcançado; não há novos resultados de conteúdo.

## Ocorrência

A conexão ao PVA (PID 14432, HWND 1510638) foi estabelecida sem modal inicial.
Ao resolver o caminho de Operações Próprias, uma categoria pai estava recolhida.
A rotina aprovada exige pais expandidos e abortou com pai_recolhido.
O segmento exato não foi persistido nesta execução. Não atribuir a uma categoria
específica sem nova inspeção.

- Cliques de ativação: zero.
- Checkbox: não inspecionado nesta tentativa e não alterado.
- Diálogo Salvar: não aberto; nenhuma confirmação.
- Operações ST: não iniciado.
- Duração total: 0,7022 s; worker inicial 0,6712 s.
- Worker terminou normalmente; nenhum timeout ou encerramento forçado.
- Configuração de acessibilidade preservada.

Pasta exclusiva criada: saida/TESTE_SUBRELATORIOS_20261113_120813 (sem PDFs).
Não houve repetição automática, expansão da árvore para contornar a falha,
troca de empresa/competência, DIFAL ou outro relatório executado.

## Verificações preparadas, ainda não executadas com salvamento

scripts/validar_dois_subrelatorios.py limita a sequência aos IDs
operacoes_proprias e operacoes_st. Reutiliza o fluxo aprovado com:

- Registro de inicial/final, mudança e busy do checkbox na abertura do relatório.
- Clique único no checkbox somente se false; nunca desmarca checked.
- Estabilidade: checked, ausência de busy e Salvar habilitado em quatro leituras;
  se houver alteração, espera mínima adicional de dois segundos antes de contar
  leituras estáveis. Esses sinais são evidência de prontidão de interface, não
  garantia isolada do término de todo processamento interno.
- Nova confirmação somente de leitura imediatamente antes de abrir Salvar;
  se o checkbox estiver false nessa confirmação, interrompe sem novo clique.
- Caminho absoluto e confirmação única, seguidos de PyMuPDF e marcadores.
- Comparação em memória com os PDFs de TESTE_TRES_RELATORIOS_20261113_115502:
  bytes, páginas, igualdade do texto normalizado e flags de marcadores novos.
  Nenhum texto fiscal é gravado. Aumento de bytes/páginas não prova inclusão.

Nesta tentativa, essas verificações de checkbox/PDF não foram alcançadas.
Não há estado inicial/final atual, recarregamento, tamanho/páginas novos ou
comparação de conteúdo a declarar. O teste anterior de inspeção havia encontrado
checked em Operações Próprias, mas esse estado histórico não substitui a
confirmação exigida imediatamente antes do novo salvamento.

## Próxima execução

Disponibilizar o caminho com seus pais expandidos antes de autorizar uma nova
tentativa, ou autorizar explicitamente uma preparação para expansão controlada
por estado. A expansão não foi implementada ou executada nesta tentativa.
Não remover travas para repetir automaticamente.

Evidências: logs/validar_subrelatorios_20261113_120813/resultado.json e
01_operacoes_proprias/relatorio/resultado.json/eventos. A configuração continua
indicando que salvamento com subrelatórios ainda não foi validado.
