# Automatizador SPED Fiscal

V2 iniciada em **Automatizador_SPED_Fiscal_V2/**, etapa de diagnóstico somente
de leitura. Menu Escrituração Fiscal → Abrir identificado, desabilitado no
estado observado. Lista de escriturações/identidade ativa ainda precisam de
inspeção autorizada. V1 preservada integralmente: 221 arquivos inalterados.

V1 independente consolidada em **Automatizador_SPED_Fiscal_V1/**.
Entrada: Iniciar.bat ou principal.py; instruções em LEIA-ME.md.
Revisão offline e nove testes aprovados, sem nova execução no PVA.
Scripts e resultados históricos preservados.

**Lote completo aprovado:** [oito PDFs gerados e verificados](docs/resultado_lote_completo_2s.md)
com espera mínima de 2 segundos, na mesma escrituração. Total: 68,7753 s.

Ordem atualizada: entradas, saídas, Próprias, ST, CIAP, Controle de Créditos
Fiscais opcional, pagamentos eletrônicos e Recibo. Recibo aguarda até 5 s com
verificações e identificação de janelas, sem fechamento/confirmacão automática.
Veja o [tratamento preparado](docs/ordem_e_espera_recibo.md). Nenhum relatório executado.

Primeiro lote completo: [resultado parcial](docs/resultado_primeiro_lote_completo.md).
Quatro PDFs validados; interrupção no Recibo antes da exportação. CIAP, saídas
e opcional não executados. Tempo total 35,6379 s; nenhuma outra empresa acessada.

Cadastro recuperado: [oito caminhos identificados](docs/cadastro_completo_recuperado.md),
oito nomes exatos definidos, incluindo Registro de Controle de Créditos Fiscais.pdf,
que permanece opcional. Nenhum relatório executado nesta atualização. As POCs anteriores
continuam limitadas aos IDs originalmente autorizados.

**Regra atual simplificada e validada:** checkbox confirmada marcada e Salvar
disponível bastam, sem exigência de estabilidade/evidência de atualização.
Operações Próprias e ST foram salvos com sucesso em 13/11/2026, 12:31.
Veja o [resultado](docs/resultado_subrelatorios_simples.md). Critérios históricos
mais restritivos abaixo foram substituídos por orientação explícita do usuário.

Diagnóstico atual: [estabilidade de subrelatórios e 16 testes offline](docs/diagnostico_estabilidade_offline.md).
Salvar habilitado/checked não bastam. Sem sinal de conteúdo do visualizador
validado, a exportação fica bloqueada. Nenhuma nova execução no PVA nesta etapa.

**Validação de subrelatórios não aprovada:** [ocorrência e correções](docs/resultado_subrelatorios_121806.md).
Operações Próprias gerou um PDF íntegro, mas um timeout de estabilidade não foi
propagado corretamente antes da gravação. A sequência parou; ST não iniciou.
Bloqueio de exportação após erro corrigido e verificado offline, sem novo salvamento.

**Navegação automática aprovada:** [expansão por estado e abertura do relatório](docs/resultado_navegacao_automatica.md).
Pais recolhidos são expandidos por toggleexpand uma única vez, com referências
Java renovadas e confirmação. O fluxo comum já usa essa navegação. Nenhum novo
PDF foi salvo; o teste de subrelatórios aguarda nova autorização.

Validação mais recente de subrelatórios: [interrompida por pai recolhido](docs/resultado_validacao_subrelatorios_interrompida.md).
Nenhum clique/PDF; Operações ST não iniciado. Estado imediatamente antes de
salvar e comparação dos PDFs com a nova regra continuam pendentes.

Regras obrigatórias atuais: [subrelatórios e exclusão de DIFAL](docs/regras_subrelatorios_e_difal.md).
Operações Próprias/ST exigem Exibir subrelatórios marcado; nos demais não há
marcação automática. DIFAL RJ/SP não integra o cadastro de geração. A opção
foi encontrada já marcada em Operações Próprias; nenhum PDF novo foi salvo.

**Sequência de três relatórios aprovada:** [resultados individuais](docs/resultado_sequencia_tres.md).
Operações Próprias, Operações ST e documentos de entradas gerados em pasta
exclusiva, com nomes exatos e conteúdo/estrutura conferidos, em 18,3267 s.
Nenhuma outra empresa ou relatório foi executado.

**Prova integrada aprovada:** [árvore até PDF, sem intervenção manual](docs/resultado_ponta_a_ponta.md).
Operações Próprias salvo em arquivo novo de 3.539 bytes/1 página, estrutura e
marcadores conferidos, em 7,9233 s. Nenhum timeout ou repetição; sem geração em lote.

Último resultado: [PDF salvo pela janela aberta fisicamente](docs/resultado_pdf_fisico.md).
Um arquivo de 3.539 bytes e 1 página passou na verificação estrutural PyMuPDF.
Houve uma única confirmação de salvamento e nenhum bloqueio. O fluxo contínuo
com a nova estratégia ainda precisa de teste próprio; não há geração em lote.

**Último resultado:** [Salvamento físico: abertura e conexão comprovadas](docs/resultado_salvar_fisico_sucesso.md).
Um clique dinâmico abriu Salvar; B obteve contexto e identificou Nome do arquivo.
Ambos os workers encerraram normalmente. Nenhum campo foi preenchido nem PDF salvo.

Última execução do [teste de Salvar físico](docs/resultado_teste_salvar_fisico.md):
interrompida antes do clique porque não havia um alvo Salvar inequívoco na
inspeção. Não abriu modal, não iniciou B e não gerou PDF.

Preparação mais recente: [clique físico dinâmico no botão Salvar](docs/preparacao_salvar_fisico.md),
sem execução do clique. A PID 25028 terminou entre as verificações de identidade;
nenhum encerramento forçado foi executado e o PVA foi preservado.

Último diagnóstico modal: [A vivo durante a conexão de B](docs/resultado_modal_concorrente.md).
B terminou normalmente, mas não reconheceu a janela Java. Nenhum PDF foi gerado.
A foi preservado após timeout de saída normal, conforme solicitado pelo usuário.

Regra atual: `selected` sozinho não comprova abertura. Um clique físico único
com posição calculada do controle Java abriu Operações Próprias e tornou Salvar
disponível. Veja o [teste de ativação real](docs/resultado_ativacao_real.md).
Essa conclusão corrige a hipótese anterior de abertura por AccessibleSelection.

O [teste completo com workers isolados](docs/resultado_fluxo_completo_isolado.md)
ativou o relatório e abriu Salvar, mas B não conseguiu reconhecer o diálogo
pela bridge. Nenhum PDF foi criado nessa prova; o fluxo completo segue pendente.

O [planejamento](docs/planejamento.md) define o futuro cadastro fixo de
relatórios: localização no PVA, nome exato do PDF fornecido pelo usuário e
empresas destinatárias explícitas. A competência poderá organizar pastas;
não será acrescentada automaticamente aos nomes dos arquivos.

Prova de conceito: diagnostico de acessibilidade Java somente de leitura.

Execute `python scripts/diagnostico.py` com o PVA ja aberto. A configuracao
fica em `config/diagnostico.toml`; resultados locais ficam em `logs/`.
Nenhuma dependencia e instalada automaticamente. Requer pyjab e pywin32.

O script nao clica, nao envia teclas, nao muda foco, nao inicia ou encerra o PVA.
Bloqueia a habilitacao automatica do Access Bridge pelo pyjab. Nao coleta
descricoes, textos fiscais ou conteudo de tabelas/listas/arvores. Nomes sao
registrados apenas por lista permitida de rotulos estaticos. Indices da arvore
sao identificadores de diagnostico, nao seletores estaveis.

A bridge configurada deve ter a mesma arquitetura do Python. O teste inicial
usa Python 32 bits e a bridge Java 8 de 32 bits existente no computador.
Compatibilidade com o runtime privado do PVA deve ser comprovada pelo teste.

## Teste isolado do campo de salvamento

Com a janela Salvar aberta manualmente, `python scripts/teste_campo_salvar.py`
inspeciona seus controles. A opcao `--preencher` substitui somente o texto do
campo Nome do arquivo pelo caminho ficticio definido no script. Nao cria pastas,
nao confirma o dialogo e nao salva PDF. Requer autorizacao para cada nova etapa
de interacao; nao integra um fluxo automatico de salvamento.

Prova de conceito do preenchimento concluída: o caminho completo fictício foi
inserido e confirmado por leitura, sem salvar o PDF. Veja o
[resultado técnico](docs/resultado_campo_salvar.md).

## Salvamento único autorizado

Concluído em 13/11/2026: PDF fictício de 28.688 bytes e 3 páginas, conferido
localmente por PyMuPDF. Veja o [resultado](docs/resultado_salvamento_unico.md).
O script `scripts/salvar_pdf_unico.py` executou uma única ação acessível Salvar.
A trava persistente e a existência do destino impedem repetir este teste.
Não executar outros salvamentos sem nova autorização do usuário.

## Diagnóstico da árvore de relatórios

`python scripts/diagnostico_arvore.py` inspeciona a aba Relatórios sem selecionar
ou expandir nós. Registra caminhos por nomes e informações acessíveis, sem
ler conteúdo fiscal. Veja o [resultado](docs/resultado_arvore.md) e a
[hierarquia observada](docs/arvore_observada.md). A seleção programática ainda
depende de teste autorizado; não existe execução em lote.

O teste posterior `scripts/selecionar_operacoes_proprias.py` confirmou mudança
de seleção na árvore com uma chamada Java, mas não confirmou o relatório no
visualizador. Veja o [resultado inconclusivo](docs/resultado_selecao_operacoes.md).
A trava persistente impede repetir a ação; nenhuma técnica alternativa foi
executada e nenhum salvamento foi realizado nessa etapa.

O critério posterior aceito pelo usuário usa `selected` sem exigir título do
visualizador. `scripts/fluxo_operacoes_proprias.py` confirmou a seleção e abriu
Salvar, mas a execução ficou aguardando antes do preenchimento e foi interrompida
sem fechar o PVA. Nenhum PDF foi criado nesse fluxo. Veja o
[resultado e alternativas](docs/resultado_fluxo_operacoes.md).

Investigação instrumentada: `scripts/investigar_modal.py`, supervisor com
workers isolados e timeout externo. O Processo A não encontrou Salvar no estado
atual do visualizador; B não foi executado e o bloqueio não foi reproduzido.
Veja as [evidências e limitações](docs/resultado_investigacao_modal.md).
