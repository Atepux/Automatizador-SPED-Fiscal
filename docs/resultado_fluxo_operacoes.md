# Fluxo único de Operações Próprias — 13/11/2026

Resultado: fluxo interrompido após abrir a janela Salvar; nenhum PDF criado.

## Critério atualizado

O usuário confirmou que a seleção normal da árvore atualiza o visualizador.
Nesta etapa, o estado selected é a confirmação exigida; um título acessível
no visualizador deixou de ser requisito. Essa orientação substitui o critério
mais restritivo do teste anterior, sem alterar os resultados históricos.

## Ações realizadas

1. Destino fictício novo definido:
   saida/TESTE_FICTICIO/teste_fluxo_operacoes_proprias.pdf. Não existia.
2. Caminho completo resolvido por nomes entre filhos imediatos:
   Escrituração Fiscal → Relatórios de Registros Fiscais → Apuração do ICMS →
   Operações Próprias. Pais expandidos e nós visíveis confirmados.
3. Uma chamada a addAccessibleSelectionFromContext, contexto do pai e índice
   do filho resolvido no momento. O nó passou de não selecionado para selected.
4. Espera de cinco segundos, sem novo diálogo detectado.
5. Botão do visualizador encontrado por papel push button e descrição Salvar,
   sem coordenadas. Uma ação Java abriu o diálogo Salvar.

## Interrupção e estado final

O script deixou de avançar após o retorno da ação que abriu o diálogo e antes
de registrar o preenchimento. A consulta externa somente de leitura confirmou
uma janela Salvar, classe SunAwtDialog, HWND 1117480, no PID 14432 do PVA.
Não foi detectada janela inesperada nessa consulta.

O processo Python do teste (PID 28848) foi identificado pela linha de comando
e interrompido isoladamente. O PVA permaneceu aberto e respondendo.
O botão de confirmação de salvamento não foi acionado e o destino continuou
inexistente. Não houve repetição da seleção nem da abertura do diálogo.

Não há tamanho/páginas ou verificação de conteúdo a informar, pois não há PDF.
A janela Salvar permaneceu aberta na última observação. Nenhuma empresa ou
competência foi trocada, nenhum outro relatório foi selecionado e nenhuma
operação sobre escriturações foi executada.

## Hipótese técnica e alternativas

A região suspeita é a conexão de uma segunda instância JABDriver ao diálogo
no mesmo processo Python, ou sua inspeção subsequente. Sem stack trace não
é possível atribuir com certeza a chamada que bloqueou. O timeout passado ao
driver não garante limite para toda chamada nativa da bridge.

Para uma próxima autorização, recomenda-se separar a seleção/abertura e o
preenchimento/salvamento em processos Python distintos, reutilizando a abordagem
de conexão direta ao diálogo que funcionou no teste isolado. Um supervisor
deverá limitar a espera das chamadas nativas e interromper apenas o processo
de diagnóstico, nunca repetir a ação. Outra opção a investigar é reutilizar a
bridge já inicializada para obter o contexto do diálogo sem criar outro driver.
Nenhuma dessas alternativas foi executada nesta etapa.

Script: scripts/fluxo_operacoes_proprias.py. Registro técnico:
logs/fluxo_operacoes_20261113_104719.json. Trava persistente:
logs/fluxo_operacoes_acionado.lock. Não remover para repetir automaticamente.
