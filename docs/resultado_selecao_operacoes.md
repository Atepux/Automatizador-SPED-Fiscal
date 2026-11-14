# Seleção de Operações Próprias — 13/11/2026

Resultado: seleção reconhecida na árvore, mas sucesso completo não comprovado.
O critério exigido inclui confirmar o relatório no visualizador, e essa
confirmação não foi obtida por nomes acessíveis.

## Procedimento executado

- PVA PID 14432, HWND 1510638, sem diálogo aberto identificado no início.
- Localização pelo caminho exato entre filhos imediatos, sem índices fixos:
  Escrituração Fiscal → Relatórios de Registros Fiscais → Apuração do ICMS →
  Operações Próprias.
- Todos os segmentos estavam visible/showing; os três pais estavam expanded.
- O pai Apuração do ICMS expôs AccessibleSelection. O índice local observado
  do filho Operações Próprias era 0; foi resolvido nesta execução.
- Antes da chamada, a folha não estava selected.
- Uma única chamada a addAccessibleSelectionFromContext, passando o VMID,
  contexto acessível do pai e índice local do filho.
- A chamada retornou sem erro. A folha passou a apresentar selected.
- Nenhuma nova janela foi detectada na espera. Configuração de acessibilidade
  preservada. Sem cliques, coordenadas, teclas, expansão ou repetição de seleção.

## Limitação do visualizador

Durante até dez segundos, a inspeção somente de leitura procurou o título
Operações Próprias em nomes de controles visíveis fora das árvores. Não houve
coincidência antes nem depois da seleção. Não foi extraído conteúdo fiscal,
texto de documentos ou imagens do relatório. A ausência desse nome não prova
que o visualizador permaneceu no relatório anterior: ele pode usar outro título
ou renderizar o cabeçalho sem nome acessível. Também não prova que foi atualizado.

Portanto, este teste comprova apenas a mudança de seleção da árvore.
Não considerar a seleção ponta a ponta concluída e não reutilizar o método
como etapa validada de geração automática.

## Alternativas propostas, não executadas

1. Confirmar visualmente o cabeçalho atual do relatório, por observação somente
   de leitura ou confirmação manual do usuário, sem executar nova seleção.
2. Inspecionar de forma direcionada os controles de identificação do visualizador
   para descobrir seu título real, preservando a privacidade dos dados fiscais.
3. Se a seleção apenas destacar a folha, mapear o comando explícito de abertura
   do relatório e testar esse comando somente com nova autorização. Não assumir
   que clique duplo ou Enter sejam necessários ou seguros antes desse mapeamento.

Script: scripts/selecionar_operacoes_proprias.py. Evidência:
logs/selecao_operacoes_20261113_103913.json.
Trava persistente: logs/selecao_operacoes_acionada.lock. Impede nova ação em
execuções posteriores, inclusive após resultado inconclusivo.
Nenhum PDF foi salvo e nenhuma empresa ou competência foi trocada.
