# Preparação do clique físico no botão Salvar — 13/11/2026

Status: preparado, não executado. Não houve novo clique ou conexão ao PVA.

## Encerramento autorizado de A

A primeira consulta confirmou o PID 25028 como python.exe da instalação
Python314-32, executando modal_concorrente.py --worker A na pasta do teste
modal_concorrente_20261113_112523. A data de criação correspondia ao teste.
Na reconfirmação imediatamente anterior ao encerramento, o processo já não
existia. A proteção abortou antes de Stop-Process. Uma consulta seguinte
confirmou sua ausência. Nenhum encerramento forçado foi executado.

O PVA PID 14432 continuou aberto e respondendo. Nenhum outro processo foi
encerrado. O resultado foi gravado em
logs/modal_concorrente_20261113_112523/encerramento_A_autorizado.json.
O motivo exato da saída espontânea de A não foi determinado nesta etapa.

## Viabilidade técnica

A biblioteca instalada oferece JABElement.click(simulate=True), cálculo do
centro do controle, conversão para coordenadas físicas e entrada de mouse.
O ramo simulate=True utiliza movimento/clique de mouse; não chama
_do_accessible_action/doAccessibleActions. É tecnicamente plausível evitar
o acoplamento síncrono da ação Java à exibição modal. Isso ainda não comprova
que a conexão ao diálogo será bem-sucedida.

O método já funcionou no nó Operações Próprias. Para o botão do visualizador,
a nova comparação deve trocar somente a forma de acionamento e manter as
verificações de PID/HWND/contexto, sem preencher campos nem salvar PDF.

## Preparação disponível

scripts/preparar_salvar_fisico.py contém:

- Verificação estática dos métodos instalados; não cria driver ou acessa o PVA.
- preparar_alvo(driver, button), função de leitura para uma futura sessão:
  exige janela principal SunAwtFrame do PVA, mesmo PID/HWND, botão com nome ou
  descrição Salvar, estados habilitado/visível, ausência de modal, primeiro
  plano e ponto físico dinâmico pertencente à janela correta.
- A função retorna limites/ponto técnicos, mas não executa clique ou altera foco.

Nenhum ponto é fixo ou persistido para reutilização. O teste futuro deve
revalidar o alvo imediatamente antes do clique para evitar mudança de layout.
A função focus() do pyjab pode enviar espaço à janela anterior; por isso o
alvo exige primeiro plano confirmado antes de qualquer click(simulate=True).

## Roteiro proposto para nova autorização

1. Supervisor com timeouts externos, A e B independentes e logs imediatos.
2. A resolve o caminho completo de Operações Próprias e abre exclusivamente
   esse relatório pelo clique dinâmico aprovado.
3. Localiza semanticamente Salvar, confirma disponibilidade e prepara o alvo.
4. Sob autorização nova, registra tentativa única e executa
   button.click(simulate=True), sem fallback ou repetição automática.
5. Supervisor detecta o diálogo esperado por PID/classe/título e inicia B
   enquanto A continua vivo. Não cria segundo driver em A.
6. B mede isJavaWindow e obtenção de contexto separadamente; lê somente nomes
   estáticos/papéis/estados se houver contexto. Não preenche ou confirma nada.
7. Compara resultados e tempos com o acionamento AccessibleAction anterior.
   Se B bloquear, encerra somente B. Se A não terminar, preserva e solicita
   autorização antes de encerrá-lo, conforme o procedimento anterior.

Não implementar lote, reutilizar índices fixos, instalar dependências ou
atribuir sucesso apenas à aparição da janela. Coordenadas/DPI, foco, janela
desobstruída e exposição Java do botão precisam ser confirmados no momento
do teste. Se uma modal já estiver aberta, interromper sem fechá-la/reabri-la.
