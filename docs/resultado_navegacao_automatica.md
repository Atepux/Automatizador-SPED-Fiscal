# Navegação automática aprovada — 13/11/2026, 12:15

Teste restrito a Operações Próprias, sem geração de PDF ou acionamento de Salvar.

| Pai do caminho | Estado inicial | Ação | Confirmação |
| --- | --- | --- | --- |
| Escrituração Fiscal | expanded | Nenhuma | Leitura expanded |
| Relatórios de Registros Fiscais | collapsed | Uma expansão toggleexpand | Nova referência retornou expanded |
| Apuração do ICMS | expanded | Nenhuma | Leitura expanded |

Após percorrer esses pais, a folha Operações Próprias foi localizada por nome
exato entre os filhos imediatos. Um único click(simulate=True), com limites
Java atuais e validação de foco/ponto, abriu o relatório. Salvar estava ausente
antes e ficou visível/habilitado depois; selected foi apenas confirmação
complementar. Abertura efetiva confirmada pelo critério aprovado do visualizador.

Duração do worker: 2,3567 segundos. Exit code 0, sem timeout ou repetição,
mesmo PVA PID 14432 e HWND principal 1510638. Configuração de acessibilidade
preservada. Não houve modal, mudança de empresa/competência ou outros relatórios.
A opção de subrelatórios não foi alterada e nenhum PDF foi salvo.

## Implementação

scripts/navegacao_arvore.py fornece localizar_expandindo(driver, path, events):

1. Localiza a árvore exclusivamente na aba Relatórios.
2. Resolve cada prefixo do caminho por nomes exatos e filhos imediatos.
3. Lê expanded/collapsed de cada pai; não age se já expanded.
4. Para collapsed/expandable, inspeciona ações e exige toggleexpand. O teste
   comprovou a ação no pai recolhido acima; não foi necessário fallback físico.
5. Chama expand(simulate=False) uma única vez, que também relê o estado antes
   de alternar. Não repete a ação durante a espera.
6. Descarta referências antigas e obtém novo contexto de janela/árvore e nós
   para confirmar expanded e resolver o próximo segmento. A espera de leitura
   é limitada a cinco segundos por expansão.
7. Interrompe por ausência/ambiguidade, modal, mudança de VMID, falta de ação
   adequada ou timeout; não tenta clicar na linha de um pai para expandi-lo.
8. Retorna somente a folha solicitada para o clique físico de abertura.

Não há coordenadas fixas. A expansão semântica é preferida ao clique físico
no indicador, evitando ativação indevida da linha. Se toggleexpand não estiver
exposto ou não expandir, a rotina interrompe; não há fallback não validado.

## Integração e limites

O worker de ativação ganhou a opção auto_expand. Após esta prova aprovada,
o fluxo comum scripts/poc_ponta_a_ponta.py passou a usar essa opção para todos
os caminhos parametrizados do cadastro. Não foi executada geração em lote ou
novo salvamento durante essa integração.

O algoritmo trata cada pai independentemente do estado inicial, incluindo
raiz ou categorias recolhidas. A execução real desta etapa encontrou apenas
Relatórios de Registros Fiscais recolhido; não foi forçado um cenário com todos
os pais recolhidos, pois isso exigiria recolher nós já expandidos. Logo, o
cenário totalmente recolhido está contemplado pelo algoritmo, mas não foi
integralmente reproduzido neste teste. O comportamento de toggleexpand em
outros tipos de nó continua sujeito à confirmação por estado em cada execução.

As regras de Exibir subrelatórios permanecem obrigatórias para Operações
Próprias/ST, sem marcação automática nos demais. DIFAL continua fora do
cadastro. A validação de salvamento com subrelatórios permanece pendente
de nova autorização; não foi retomada automaticamente.

Script de teste: scripts/testar_navegacao_arvore.py, timeout externo de 30 s,
trava persistente de autorização e ausência de qualquer comando de salvamento.
Evidências: logs/navegacao_auto_20261113_121537/resultado.json,
resultado.navegacao.jsonl e resumo.json. Compilação sintática aprovada.
