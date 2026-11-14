# Espera de subrelatórios: diagnóstico e testes offline — 13/11/2026

Nenhum acesso ao PVA, clique, leitura de janela ou salvamento nesta etapa.
A informação do usuário foi incorporada: o estado normal inicial pode ser
desmarcado. Nunca presumir checked por causa de uma execução anterior.

## O que causou o timeout

O log histórico prova inicial false, uma ação de marcação e retorno dessa ação
em 0,401246 s. Em seguida houve TimeoutError; não foram gravados os valores de
cada amostra. Portanto, a condição booleana específica que impediu a contagem
de estabilidade NÃO pode ser identificada retrospectivamente com certeza.

Na versão executada, a espera exigia checked, ausência de busy, Salvar
habilitado, espera mínima e quatro observações consecutivas. Não exigia que
busy aparecesse em algum momento. Não há fundamento para dizer que aguardava
obrigatoriamente um evento busy que o PVA nunca emite.

A causa provável é a referência antiga de Salvar, capturada antes da marcação:
o checkbox pode reconstruir o visualizador, deixando o controle antigo sem os
estados esperados. A conexão posterior encontrou checked=true e Salvar pronto,
mas em outra sessão e outro instante; isso sustenta a hipótese sem prová-la.
Outras possibilidades são reconstrução demorada ou estados não expostos como
esperado. Não aumentar/remover timeout para contornar a falta de evidência.

Há dois problemas distintos: o timeout sem observabilidade suficiente e a
propagação indevida de sucesso anterior. O segundo é comprovado pelo registro
sucesso=true junto de erro_tipo=TimeoutError e foi corrigido independentemente
da causa do primeiro.

## Disponibilidade não é atualização

Salvar habilitado indica que o comando pode ser acionado, mas não que o
conteúdo novo terminou de ser construído. Checked confirma a opção; não prova
a renderização. Ausência de busy não comprova conclusão se o PVA nunca informa
esse estado. Comparar só toolbar/checkbox, bytes de PDF ou esperar dois segundos
também não resolve essa distinção.

## Critério verificável preparado

scripts/estabilidade_relatorio.py separa o monitor de estabilidade da interface.
O adaptador deve observar conteúdo REAL do visualizador, excluindo árvore,
toolbar e checkbox. Sinais candidatos a mapear em próxima inspeção autorizada:
identidade/geração dos componentes de páginas renderizadas, indicador explícito
de carregamento e impressão digital do conteúdo visível mantida só em memória.
Não foi assumido que qualquer desses sinais já esteja disponível no PVA.

Após mudança false→true, exigir evidência de atualização: conteúdo diferente
do anterior ou ciclo de carregamento observado até conclusão. Depois exigir
conteúdo presente e constante, carregamento explicitamente encerrado, checkbox
true e Salvar habilitado, por ao menos três amostras e intervalo contínuo de
0,75 s, dentro do timeout total de 10 s. Conteúdo que oscila reinicia a janela;
carregamento desconhecido, conteúdo ausente ou erro de leitura não são aceitos.
Se já checked, não clicar; ainda exigir conteúdo observável e estável, sem
exigir uma nova transição que a automação não provocou.

O intervalo temporal é requisito adicional a estados/conteúdo observáveis,
nunca uma espera fixa usada sozinha como prova. Mesmo esse critério depende
da validação do sinal fornecido pelo adaptador; a heurística não deve ser
anunciada como garantia da lógica interna do PVA.

## Bloqueio obrigatório e integração

garantir_subrelatorios agora recebe observar_conteudo como dependência explícita.
Sem provedor validado, lança SinalConteudoIndisponivel ANTES de marcar ou exportar.
Não há fallback para checked+Salvar. O fluxo atual propositalmente não poderá
voltar a gerar os dois relatórios até mapear/ligar esse sinal em teste autorizado.

O contexto, checkbox e Salvar são redescobertos a cada leitura. Amostras gravam
somente booleanos de prontidão/transição; tokens e conteúdo fiscal não são
persistidos. A espera não repete a ação de marcação.

Qualquer exceção na ativação define sucesso=false. Falhas de liberação/detach
também impedem sucesso. O supervisor rejeita erro_tipo mesmo com sucesso residual,
e exige final, estabilidade, Salvar, sinal de conteúdo e atualização confirmados
antes de lançar o processo abrir_salvar. Falta/null de resultado bloqueiam.
O processo de abertura ainda faz sua confirmação final antes de clicar; qualquer
falha impede a abertura do diálogo. Timeouts externos dos workers permanecem.

## Testes offline

Comando: python -m unittest discover -s tests -p test_estabilidade_offline.py -v

16 testes aprovados, com relógio virtual, observações e subprocessos simulados.
Nenhum processo real foi criado pelos testes. Incluem:

- Timeout com Salvar habilitado, mas sem evidência de atualização.
- Checkbox não confirmada; carregamento permanente ou desconhecido.
- Conteúdo ausente ou permanentemente variável.
- Atualização observada e conteúdo estabilizado permitindo prosseguir.
- Checkbox já true sem necessidade de nova transição.
- Exceções do observador e do registrador propagadas.
- Fixture sanitizada do erro real sucesso=true/TimeoutError sendo rejeitada.
- Resultados incompletos/null sem chamar exportação.
- Supervisor real com Popen/Win32 simulados: somente o worker de ativação é
  lançado, nunca abrir_salvar/gravar, diante de timeout ou prontidão incompleta.

Não são testes de comportamento real do PVA. A montagem e validação do provedor
do visualizador, bem como a nova transição false→true e atualização, permanecem
pendentes. Não foi reexecutada a sequência nem gerado PDF nesta etapa.
