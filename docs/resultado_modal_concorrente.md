# Modal com A vivo durante B — 13/11/2026

Resultado: manter A vivo não tornou o diálogo acessível a B neste teste.
Nenhum campo foi preenchido, nenhum salvamento confirmado e nenhum PDF gerado.

## Coordenação executada

- Supervisor Python independente, sem carregar a bridge.
- A (PID 25028) resolveu exclusivamente o caminho de Operações Próprias,
  confirmou pais expandidos e ativou a folha por um clique físico dinâmico.
- Salvar passou de ausente para disponível no visualizador. A acionou uma
  única ação acessível Salvar, sem repetir cliques.
- Supervisor detectou SunAwtDialog/Salvar, HWND 134994, no PVA PID 14432,
  com janela principal HWND 1510638. Iniciou B sem esperar retorno/saída de A.
- B (PID 32172) recebeu somente PID/HWND, não referências Java de A.
- A permaneceu vivo durante toda a execução de B. Não foi encerrado à força.

## Resultados separados de B

| Operação | Resultado | Duração |
| --- | --- | ---: |
| Service.__init__ | Retornou | 0,004629 s |
| Carregamento da DLL | Retornou | 0,002801 s |
| Configuração de assinaturas ctypes | Retornou | 0,001572 s |
| Windows_run | Retornou | 0,016300 s |
| Atendimento inicial da fila de mensagens | Executado por aproximadamente 1 s | 1,017199 s |
| isJavaWindow(HWND) | False | 0,013160 s |
| getAccessibleContextFromHWND | False; VMID 0; contexto nulo | 0,001589 s |

Como não houve contexto válido, nenhuma leitura de controles Java foi tentada.
Nenhum conteúdo de campo, nome de empresa ou dado fiscal foi registrado.
B finalizou normalmente (exit code 0), sem bloqueio e sem necessidade de kill.
O exit code informa término normal do diagnóstico, não sucesso da conexão.

## Linha do tempo (UTC; horário local = UTC−3)

| Evento | Timestamp UTC |
| --- | --- |
| Início de A | 14:25:23.650 |
| Antes de A acionar Salvar | 14:25:25.051 |
| Modal detectada pelo supervisor | 14:25:25.493 |
| B iniciado com A vivo | 14:25:25.506 |
| B concluído com A vivo | 14:25:26.793 |
| Retorno da ação Salvar em A | 14:25:33.075 |
| Saída normal de A solicitada após B | 14:25:33.089 |

B foi iniciado aproximadamente 13 ms após detectar a janela e cerca de
6,5 segundos antes do retorno da ação em A. Assim, a tentativa de B aconteceu
enquanto a ação de abertura ainda estava pendente em A, não apenas enquanto
o processo existia. A ação demorou cerca de 8,024 segundos para retornar.

## Timeouts e estado de A

O supervisor limita a fase de abertura a 30 s, B a 20 s e a saída normal de
A a 8 s após B terminar. B não atingiu timeout. A não terminou no prazo após
ser liberado pelo supervisor e permaneceu ativo. O último evento de A foi
B_concluido_saida_normal_solicitada, antes da limpeza de referências/driver.
Sem instrumentação individual nessa limpeza, não atribuir a espera a uma
função específica.

A consulta posterior confirmou A PID 25028 e PVA PID 14432 ainda em execução.
O supervisor não possui chamada de kill para A. Não encerrar esse processo sem
a autorização adicional exigida pelo usuário. O processo foi iniciado sem
janela de terminal visível. Configuração de acessibilidade preservada.

## Comparação e interpretação

No teste isolado, o diálogo aberto manualmente foi reconhecido e seus campos
foram acessados. No fluxo serial anterior, B só iniciou após a morte de A e
não obteve contexto. Agora B iniciou imediatamente com A vivo e a falha
persistiu: reconhecimento false e contexto false/nulo.

Logo, encerrar A não é condição necessária para ocorrer a falha. Isso não
prova que encerrar A jamais interfira. Tampouco descarta que B pudesse conectar
depois do retorno da ação, com A vivo: esse cenário não foi testado e não houve
nova tentativa automática.

A evidência desloca a investigação para a ação acessível que abre a modal e
para o registro/comunicação da bridge enquanto ela está pendente. Oito segundos
de retorno recorrentes são um indício a investigar, não prova de timeout nativo.

Proposta para nova autorização: comparar a abertura de Salvar por um único
clique físico dinâmico no botão Java, mantendo o cliente vivo, com a atual
abertura por AccessibleAction. Outra comparação possível é testar B somente
depois do retorno da ação, com A ainda vivo. Não executar ambas automaticamente
nem repetir cliques. Nenhuma dessas alternativas foi testada nesta etapa.

## Arquivos

- scripts/modal_concorrente.py: supervisor, worker B de leitura e logs imediatos.
- scripts/ativar_operacoes_proprias.py: opção de manter A vivo até sinal de B.
- logs/modal_concorrente_20261113_112523/resultado.json.
- Na mesma pasta: supervisor.jsonl, A.json, A.eventos.jsonl,
  B.resultado.json e B.eventos.jsonl.

Scripts passaram por compilação sintática. Não foram instaladas bibliotecas,
trocadas empresa/competência ou executadas operações sobre escriturações.
