# Salvar por clique físico dinâmico — 13/11/2026, 11:46

Critério desta prova atendido: um clique físico abriu o diálogo e B reconheceu
a janela Java, obteve contexto e identificou Nome do arquivo. Não houve
preenchimento nem confirmação de salvamento, tampouco geração de PDF.

O usuário esclareceu que o teste anterior ocorreu sem relatório aberto e
autorizou nova tentativa. Antes da execução, foi confirmado no registro anterior
que nenhum clique tinha ocorrido. O relatório atualmente aberto foi mantido;
não houve navegação pela árvore nem troca de empresa ou competência.

## Resultado

- PVA PID 14432, HWND principal 1510638, sem indicação de travamento e sem
  modal inicial.
- A PID 31456 localizou um único botão Salvar visível/habilitado pelo nome ou
  descrição Java. Foco, limites e ponto físico foram verificados imediatamente
  antes da interação, usando preparar_alvo de preparar_salvar_fisico.py.
- Executado uma única vez button.click(simulate=True), sem doAccessibleActions.
- Supervisor detectou Salvar / SunAwtDialog, HWND 1249104, no mesmo PVA.
- B PID 16124 iniciou enquanto A permanecia vivo.
- isJavaWindow: true.
- getAccessibleContextFromHWND: true, VMID 1772740, contexto não nulo.
- Leitura de 70 controles, com campo text de nome Nome do arquivo:, visível,
  habilitado, editável e single line. Salvar/Cancelar também identificados.
- B e A terminaram normalmente (exit code 0), sem timeout ou kill.
- Configuração de acessibilidade preservada. Nenhuma biblioteca instalada.

## Tempos

| Operação | Duração |
| --- | ---: |
| Localização de Salvar | 0,288400 s |
| Preparação e recálculo do alvo | 0,008094 s |
| click(simulate=True) | 0,009555 s |
| isJavaWindow em B | 0,007778 s |
| Obtenção de contexto em B | 0,001560 s |
| Leitura dos controles em B | 0,183124 s |
| Supervisor completo | 3,594400 s |

O bombeamento inicial da fila de B foi mantido em aproximadamente um segundo,
como no teste concorrente anterior. Logs contêm timestamps UTC.

## Interpretação e limites

No teste anterior, com abertura via ação acessível, B retornou false/contexto
nulo mesmo com A vivo, e A não saiu no prazo. Nesta execução, usando clique
físico no botão, B conectou e ambos saíram normalmente. O resultado sustenta
adotar clique físico dinâmico como método de abertura de Salvar nesta POC,
sem atribuir com certeza a uma função interna o mecanismo do bloqueio anterior.

Requer janela visível, desobstruída, foco confirmado, limites Java válidos e
conversão DPI adequada. Só foi comprovado no ambiente atual e nesta execução.
Não comprova ainda o fluxo completo até PDF usando esse novo método.

A janela Salvar foi deixada aberta. Não foram lidos os valores de campos ou
conteúdo fiscal, apenas nomes estáticos, papéis e estados. Não houve técnica
alternativa ou repetição de clique nesta execução.

Evidências: logs/salvar_fisico_20261113_114615/resultado.json, A.resultado.json,
A.eventos.jsonl, B.resultado.json e B.eventos.jsonl.
Script: scripts/testar_salvar_fisico.py. A nova autorização foi registrada
separadamente sem remover as travas dos testes anteriores.
