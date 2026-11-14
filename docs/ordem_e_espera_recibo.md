# Ordem e espera de Recibo — atualização sem execução

Ordem obrigatória gravada no cadastro:

1. Documentos de entradas.
2. Documentos de saídas.
3. Operações Próprias.
4. Operações ST.
5. CIAP.
6. Registro de Controle de Créditos Fiscais (opcional).
7. Operações com Instrumentos de Pagamentos Eletrônicos.
8. Recibo.

Nomes de saída preservados. Subrelatórios somente para Próprias/ST, por regra
simples de is_checked e Salvar disponível, sem estabilidade adicional. Opcional
ausente continua ignorado. Expansão por estado, nomes exatos, proibição de
sobrescrita e não repetição de cliques permanecem.

## Recibo

Cadastro define timeout_abertura_segundos=5. Após o clique único na folha,
o worker verifica seleção, disponibilidade/habilitação de Salvar e janelas
adicionais do mesmo PID durante até cinco segundos. Se o estado necessário
estiver disponível antes, continua imediatamente. Não usa sleep(5) fixo.
Uma janela adicional não causa recusa imediata nesse intervalo.

Antes de decidir, registra HWND, PID, classe, owner, visibilidade e identificação
de título por lista segura. Títulos potencialmente fiscais não são gravados.
Esses dados ajudam a distinguir uma janela do Recibo de outro tipo de modal;
um indício no título não autoriza clicar nem tratar a janela como Salvar.

Se a janela transitória desaparecer e os controles esperados estiverem prontos,
o fluxo prossegue. Se uma janela adicional permanecer ao final do prazo,
registra pendente_identificacao_janela e suspende a sequência para mapeamento
da janela real. Não fecha, confirma ou manipula janelas desconhecidas. A espera
adicional do supervisor usa o mesmo prazo da ativação, sem reiniciar cinco
segundos nem repetir a abertura.

Não foi presumido suporte a uma segunda janela de visualização: se o Recibo
usar outra janela permanente, será necessário identificar seus controles antes
de implementar a continuação nela. Ausência de janela extra, mas controles
indisponíveis ao final do prazo, resulta em falha de prontidão.

## Investigação da falha anterior

No primeiro lote, o worker do Recibo terminou com seleção e Salvar disponíveis,
mas o supervisor recusou continuar antes de criar o worker abrir_salvar.
O trecho antigo comparava o conjunto de janelas ao inicial e rejeitava qualquer
diferença. Não persistia a janela observada ou a causa detalhada. A consulta
posterior encontrou somente a principal. Logo, a identidade histórica não pode
ser recuperada com certeza nem classificada retrospectivamente como erro real.
O novo tratamento coleta os identificadores antes de decidir e tolera a janela
durante a espera limitada, sem assumir que ela seja indevida.

Atualizados cadastro, worker de ativação e supervisor compartilhados, além da
preservação do status pendente no lote. Conferência apenas sintática/configuração,
sem testes de interface, cliques, execução de relatórios ou geração de PDFs.
