# Diagnóstico da árvore de relatórios — 13/11/2026

Conexão pyjab bem-sucedida com o PVA, PID 14432 e HWND 1510638. Foi localizada
uma árvore Java (`tree`) exclusivamente dentro da aba Relatórios. A leitura
registrou nomes, papéis, estados, relações pai/filho, caminhos por nomes e
índices, interfaces e ações acessíveis. Nenhuma ação de interface foi executada.

A [hierarquia observada](arvore_observada.md) apresenta os rótulos encontrados.
Exemplos de caminhos completos:

- Escrituração Fiscal → Relatórios de Registros Fiscais → Documentos → Entradas de Mercadorias e Aquisição de Serviços.
- Escrituração Fiscal → Relatórios de Registros Fiscais → Apuração do ICMS → Operações Próprias.
- Escrituração Fiscal → Apuração do IPI → Apuração do IPI.
- Escrituração Fiscal → Inventário Físico → Totais do Inventário.

Os nós são expostos como `label`, não como `tree item`. Seus nomes acessíveis
permitem identificação individual pelo caminho. O exemplo do IPI mostra por
que buscar somente o nome global pode retornar a categoria em vez da folha.
O relatório Entradas de Mercadorias e Aquisição de Serviços já estava com
estado `selected`; o script apenas leu esse estado.

## Métodos disponíveis e recomendação

A árvore e os nós com filhos expõem a interface AccessibleSelection. As
categorias expõem `toggleexpand`; as folhas retornaram zero ações disponíveis,
embora o indicador accessibleAction esteja ativo. Portanto, não presumir que
`click(simulate=False)` funcione numa folha. A API pública `select()` da versão
instalada do pyjab aceita combo box, page tab list, list e menu, mas não tree.

Recomendação para um próximo teste autorizado:

1. Partir da aba Relatórios e da árvore; resolver cada segmento do caminho por
   nome exato entre os filhos imediatos. Interromper em ausência ou ambiguidade.
2. Obter novamente o contexto do pai e o índice local do filho identificado,
   sem reutilizar índices fixos de um diagnóstico anterior.
3. Testar `driver.bridge.addAccessibleSelectionFromContext(vmid,
   contexto_do_pai, indice_do_filho)`. O pyjab também possui o auxiliar privado
   `_add_accessible_selection_from_context`. A interface de seleção do pai foi
   observada, mas o efeito dessa chamada no PVA ainda não foi testado.
4. Confirmar a seleção pela leitura do estado `selected` e pelo caminho do nó.
   Verificar separadamente se selecionar apenas destaca ou também apresenta
   o relatório. Não inferir que a seleção equivale à geração.

Se futuramente for preciso expandir uma categoria, verificar primeiro o estado
expanded/collapsed e usar a ação acessível `toggleexpand` apenas com autorização.
Não foi necessário expandir nesta leitura. Coordenadas não são a primeira opção.

## Limites e privacidade

As categorias encontradas estavam expandidas e expuseram seus descendentes;
isso não comprova o comportamento com categorias recolhidas, outras empresas
ou outras versões do PVA. A leitura foi limitada a 22 níveis e 700 controles,
sem indicação de truncamento nesta execução. Não houve leitura do conteúdo
do relatório, tabelas fiscais ou árvore de empresas. Os rótulos de relatórios
não definem nomes de arquivo ou aplicabilidade às empresas.

Nenhum relatório foi selecionado, gerado ou salvo; nenhuma empresa foi trocada.
Configuração de acessibilidade preservada. Script compilado sem erro sintático.
Evidência: logs/arvore_20261113_103518.json.
