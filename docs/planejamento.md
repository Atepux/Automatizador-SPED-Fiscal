# Planejamento do Automatizador SPED Fiscal

V2, 13/11/2026 às 15:44: menu Abrir acionado sob autorização, com fechamento
dispensado porque nenhuma escrituração estava aberta. Janela Abrir Escrituração
identificada: tabela Java com CPF/CNPJ, Data Inicial/Final e seis outras colunas;
Ok e Cancelar acessíveis. Nenhuma seleção ou confirmação de linha. Procedimento
proposto por CNPJ/período exatos em V2/docs/janela_abrir_escrituracao.md.

## V2 — preparação e diagnóstico inicial

V1 confirmada funcional pelo usuário e preservada integralmente. Pasta V2
independente criada com componentes copiados, sem modificar a origem. Inspeção
Java somente de leitura identificou Escrituração Fiscal → Abrir (sem enabled)
e Fechar (enabled). A lista de escriturações não foi aberta, nem confirmados
controles de CNPJ/período ou verificação da identidade após abertura. Proposta:
comparar identificador fiscal e datas exatas em memória, exigir correspondência
única e confirmação posterior antes dos PDFs. Nenhuma seleção/geração foi feita.
Detalhes em Automatizador_SPED_Fiscal_V2/docs/diagnostico_selecao.md.

## V1 independente preparada

Automatizador_SPED_Fiscal_V1 contém nove rotinas aprovadas copiadas sem mudança,
principal.py, configurações próprias, iniciador .bat, instruções e resumos
JSON/CSV por execução. Destino escolhido antes do lote ou configurado; conflitos
de nomes bloqueados antes de agir. Nove testes offline e revisão do .bat em modo
--verificar aprovados, sem acesso ao PVA. Validação real da embalagem V1 aguarda
autorização. Nenhuma troca automática de empresas/competências implementada.

Lote completo aprovado em 13/11/2026, 15:14: oito PDFs, incluindo o opcional,
gerados na nova ordem com espera mínima de 2 s, sem falha ou sobrescrita.
PyMuPDF validou todos; tempo total 68,7753 s. Nenhuma outra empresa acessada.
Veja o [resultado](resultado_lote_completo_2s.md).

Espera mínima de 2 segundos após clicar em qualquer relatório, antes de
consultar a prontidão e avançar para Salvar. Configurada em diagnostico.toml;
não substitui a confirmação do botão habilitado. Recibo mantém o prazo total
de até 5 segundos após o clique, incluindo essa espera inicial. Alteração
preparada sem executar relatórios ou gerar novos PDFs.

Último lote autorizado, 13/11/2026 às 15:12: nova ordem aplicada, Entradas
gerado e validado (28.688 bytes/3 páginas). Janela inesperada após clique em
Saídas interrompeu a execução antes de salvar; demais itens, incluindo Recibo
e opcional, não iniciados. Total 10,9685 s. Nenhuma retomada automática.
Veja o [resultado](resultado_lote_nova_ordem.md).

## Nova ordem obrigatória e Recibo

Entradas → saídas → Próprias → ST → CIAP → Controle de Créditos Fiscais opcional
→ pagamentos eletrônicos → Recibo. Nomes e regras anteriores preservados.
Recibo verifica controles/janelas por até 5 s e prossegue assim que pronto;
janela diferente é identificada antes da decisão, sem fechamento/confirmação.
Janela persistente não mapeada deixa pendência e suspende o lote. Não houve
execução nesta atualização. Veja o [detalhamento](ordem_e_espera_recibo.md).

## Primeiro lote do cadastro ampliado — parcial

13/11/2026, 15:05: gerados e validados Próprias, ST, entradas e pagamentos
eletrônicos. Interrupção de verificação de janelas após ativar Recibo, sem
exportá-lo. CIAP, saídas e opcional não iniciados; nenhuma continuação automática
ou outra empresa. Total 35,6379 s. Veja o [resultado](resultado_primeiro_lote_completo.md).

Nome do opcional confirmado: Registro de Controle de Créditos Fiscais.pdf.
Entrada habilitada, mantendo a política de ignorar quando indisponível e de
não alterar subrelatórios. Todos os oito nomes e caminhos estão definidos;
nenhum relatório foi executado nesta atualização.

## Cadastro original recuperado

Cadastro ampliado para oito entradas, com caminhos conferidos no diagnóstico
Java já existente. Sete nomes oficiais definidos; falta apenas o nome exato
do PDF de Registro de Controle de Créditos Fiscais (opcional). Esse item fica
desabilitado até confirmação e deverá ser ignorado sem interromper o lote
quando indisponível. Sem DIFAL; somente Próprias/ST alteram subrelatórios.
Nenhuma geração executada. Veja o [cadastro completo](cadastro_completo_recuperado.md).

## Regra vigente simplificada — validada em 13/11/2026, 12:31

Para Operações Próprias/ST: localizar checkbox, consultar is_checked, marcar uma
vez somente se false, confirmar true e Salvar disponível, então exportar pelo
fluxo aprovado. Removidas exigências de estabilidade, busy, transição e sinal
de conteúdo. Exceções ainda bloqueiam; timeouts externos, expansão automática,
nomes exatos e exclusão de DIFAL preservados. Não presumir checked inicial.
8 testes offline passaram e os dois PDFs foram gerados em nova pasta sem
sobrescrita. Veja o [resultado](resultado_subrelatorios_simples.md).
Esta regra substitui os critérios históricos documentados abaixo.

## Diagnóstico offline da estabilidade

16 testes offline aprovados; timeout/checkbox/atualização incompletos bloqueiam
o processo abrir_salvar. Causa provável histórica: referência antiga de Salvar,
sem amostras suficientes para comprovar qual condição causou o timeout.
O monitor agora exige conteúdo observável e estável e evidência de atualização
quando a opção muda. O adaptador desse sinal no PVA ainda precisa de inspeção
e validação autorizadas; sem ele, a rotina bloqueia antes de marcar/exportar.
Não houve clique ou novo PDF. Veja o [diagnóstico](diagnostico_estabilidade_offline.md).

## Situação atual da validação de subrelatórios

13/11/2026, 12:18: validação NÃO APROVADA. Operações Próprias foi marcada uma
vez e teve checkbox confirmado true antes da exportação, com PDF íntegro de
18.624 bytes/3 páginas. Contudo, ocorreu TimeoutError de estabilidade anterior
que não foi corretamente propagado; a gravação não deveria ter avançado.
ST não foi iniciado. Proteções corrigidas e verificadas offline, sem nova
execução. Evidência adicional de subrelatórios no conteúdo segue inconclusiva.
Veja o [registro completo](resultado_subrelatorios_121806.md).

## Navegação automática aprovada

Em 13/11/2026, 12:15, a rotina expandiu Relatórios de Registros Fiscais uma
única vez por toggleexpand, preservou os outros pais já expandidos e abriu
Operações Próprias. Salvar passou de ausente a disponível. Referências Java
foram atualizadas após a expansão. Nenhum PDF foi salvo. A função foi ligada
ao fluxo comum de todos os caminhos cadastrados, sem reexecutar geração.
Veja o [resultado e limites](resultado_navegacao_automatica.md).

A validação do salvamento com subrelatórios continua pendente de autorização.
Não retomá-la automaticamente após esta prova de navegação.

## Validação de subrelatórios pendente

Em 13/11/2026, 12:08, a sequência autorizada somente de Operações Próprias/ST
foi interrompida ao encontrar pai recolhido no primeiro caminho. Nenhum clique,
checkbox alterado ou PDF salvo; ST não iniciado. Foram preparadas confirmação
final antes de exportar e comparação local com os PDFs anteriores, mas não
alcançadas nesta tentativa. Não considerar a nova regra de subrelatórios
validada em salvamento. Veja o [resultado](resultado_validacao_subrelatorios_interrompida.md).

## Regras obrigatórias mais recentes

Operações Próprias e Operações ST exigem Exibir subrelatórios marcado antes de
salvar. Ler checked; marcar uma vez somente se false; confirmar por leitura e
redescobrir Salvar após estabilização. Não marcar automaticamente nos demais.
DIFAL RJ/SP excluídos do escopo e ausentes do cadastro executável.

Na prova de 13/11/2026, 11:59, a opção Exibir subrelatórios... foi identificada
como check box com ação clicar e estado checked. Não foi alterada e nenhum
PDF foi salvo. Integração preparada; alteração/recarregamento e conteúdo PDF
com a nova regra ainda não testados. Veja as
[evidências e limitações](regras_subrelatorios_e_difal.md).

## Estado atual — sequência controlada de três aprovada

13/11/2026, 11:55: Operações Próprias, Operações ST e documentos de entradas
foram gerados consecutivamente na mesma escrituração, em pasta exclusiva de
teste. Nomes exatos fornecidos pelo usuário preservados; PyMuPDF e marcadores
confirmados nos três PDFs, diálogo fechado entre itens. Total 18,3267 s, sem
falha, retry ou intervenção manual. Veja os
[resultados individuais](resultado_sequencia_tres.md).

O cadastro de teste contém somente estes três caminhos/nomes; não atribui
relatórios às demais empresas. Nenhuma execução para outras empresas foi feita.
Os resultados abaixo preservam as etapas históricas anteriores.

## Estado atual — prova integrada aprovada

Em 13/11/2026, 11:52, uma única execução coordenada abriu Operações Próprias
pela árvore, abriu Salvar por clique físico dinâmico, conectou ao diálogo em
outro processo e gravou/verificou um PDF novo, sem intervenção manual.
Arquivo de 3.539 bytes e 1 página; marcadores do relatório encontrados em
memória, sem conteúdo fiscal nos logs. Total 7,9233 s, sem timeout, sobrescrita
ou repetição. Veja o [resultado completo](resultado_ponta_a_ponta.md).

Os registros abaixo mantêm o histórico. A integração com essa estratégia está
comprovada para este relatório e ambiente; nenhuma geração em lote foi iniciada.
O cadastro de nomes exatos e empresas destinatárias permanece pendente de
informações do usuário, sem inferências a partir do teste fictício.

13/11/2026, 11:48: concluído o salvamento autorizado na janela Salvar deixada
aberta pelo clique físico anterior. relatorio_teste_fisico.pdf, 3.539 bytes,
1 página, válido estruturalmente no PyMuPDF. Uma confirmação, sem sobrescrita,
timeout ou nova seleção. Abertura e gravação comprovadas em etapas separadas;
o fluxo contínuo com essa estratégia e a geração em lote não foram executados.
Veja o [resultado](resultado_pdf_fisico.md).

Atualização de 13/11/2026, 11:46: nova tentativa autorizada com relatório aberto.
O clique físico dinâmico em Salvar abriu a modal; B reconheceu a janela,
obteve contexto e identificou Nome do arquivo. A/B finalizaram sem bloqueio.
Método de abertura recomendado nesta POC: click(simulate=True) no botão Java
localizado semanticamente, com foco e limites dinâmicos conferidos. Nenhum
campo foi preenchido e o salvamento com esse novo fluxo segue sem teste.
Veja o [resultado aprovado](resultado_salvar_fisico_sucesso.md).

Teste autorizado do clique físico em Salvar: execução interrompida em
13/11/2026 antes de qualquer clique, pois a inspeção do visualizador não
identificou Salvar de forma inequívoca. A terminou normalmente; B não iniciou.
O efeito desse clique sobre a conexão modal permanece sem comprovação. Veja o
[resultado](resultado_teste_salvar_fisico.md).

Atualização de encerramento: o PID A 25028 já estava ausente na reconfirmação
anterior ao Stop-Process; nenhum processo foi encerrado à força. O PVA foi
confirmado aberto e respondendo. Foi preparado apenas o teste de Salvar por
clique físico dinâmico, sem acionar o botão. Nova execução depende de nova
autorização. Veja a [preparação técnica](preparacao_salvar_fisico.md).

Investigação modal mais recente: B foi iniciado assim que Salvar apareceu,
mantendo A vivo. isJavaWindow e obtenção de contexto retornaram false; não houve
leitura de controles, preenchimento ou gravação. A permaneceu ativo após o
prazo de saída normal, aguardando autorização para encerramento. Manter A vivo
não resolveu a falha neste teste. Veja o
[resultado concorrente](resultado_modal_concorrente.md).

## Regra atual de abertura de relatórios

O estado `selected` não comprova que o relatório foi aberto. A observação mais
recente do usuário corrige a suposição anterior de atualização automática.
O teste de 13/11/2026 comprovou que um único clique físico em Operações Próprias,
com posição calculada pelos limites Java atuais, disponibiliza Salvar no
visualizador. Não foram usadas coordenadas fixas nem salvo PDF nessa etapa.
Veja o [método comprovado e suas limitações](resultado_ativacao_real.md).

Os registros abaixo preservam a sequência histórica; critérios anteriores que
aceitavam somente `selected` estão substituídos por esta regra.

## Integração de abertura e gravação

O teste completo com clique dinâmico e workers separados abriu o diálogo, mas
não alcançou a gravação. A permaneceu ativo ao solicitar saída sob modal e foi
finalizado por timeout; B encontrou o diálogo pelo Win32, mas a bridge não o
reconheceu. Nenhum PDF foi criado. A integração permanece pendente e não está
liberada para múltiplos relatórios. Veja os
[tempos e evidências](resultado_fluxo_completo_isolado.md).

## Cadastro fixo de relatórios

Os nomes dos PDFs serão os nomes exatos já utilizados e fornecidos pelo usuário.
Esta regra substitui a proposta inicial de gerar nomes com empresa, CNPJ e
competência. Nenhum desses dados será acrescentado automaticamente ao nome.

Cada entrada do futuro cadastro, separado do código, deverá conter:

| Campo | Regra |
| --- | --- |
| Identificação interna | Referência do cadastro, sem modificar o nome do PDF. |
| Localização no PVA | Caminho na árvore de relatórios ou identificação acessível inequívoca, confirmada na inspeção. |
| Nome exato do PDF | Nome completo informado pelo usuário, preservando acentos, espaços, maiúsculas, minúsculas e abreviações. |
| Empresas destinatárias | Relação explícita das empresas para as quais o relatório deverá ser gerado. |

Não inferir nomes de arquivos a partir dos rótulos do PVA. Não presumir que um
relatório seja necessário para todas as empresas. Ausência de relação de
empresas significa cadastro pendente, nunca autorização para gerar para todas.
Nenhum nome real ou vínculo relatório–empresa foi fornecido até esta etapa;
o cadastro de produção permanece pendente, sem entradas presumidas.

Os nomes fornecidos não serão normalizados, abreviados, corrigidos ou
substituídos silenciosamente. Se houver nome incompatível com o Windows,
extensão ausente ou colisão de destinos, a pendência será apresentada ao
usuário antes de usar outro nome. Arquivos existentes não serão sobrescritos
automaticamente e não haverá sufixos automáticos para contornar colisões.

## Organização dos destinos

Cada empresa terá sua própria pasta. A competência poderá ser uma subpasta,
configurada separadamente do nome do arquivo:

```text
<pasta de saída>/<pasta da empresa>/<competência opcional>/<nome exato cadastrado>
```

A montagem do caminho combinará a pasta de destino com o nome literal do
cadastro. A competência não será acrescentada ao nome do PDF. Se o próprio
nome fornecido já contiver competência ou qualquer outro dado, ele será
preservado como recebido.

## Estado da prova de conceito

1. Conexão pyjab com o PVA: concluída.
2. Inspeção da janela Salvar e identificação do campo Nome do arquivo:
   concluídas.
3. Preenchimento programático de caminho completo fictício e confirmação por
   leitura do campo: concluídos em 13/11/2026, conforme
   [resultado do teste](resultado_campo_salvar.md).

O teste comprovou entrada e leitura integral do caminho, incluindo espaços e
extensão .pdf. A janela permaneceu aberta e o PDF não foi salvo. O nome
relatorio_teste.pdf pertence apenas ao teste fictício; não define nomes do
cadastro de produção.

4. Salvamento único autorizado: concluído em 13/11/2026. O destino foi
   confirmado como inexistente, o caminho absoluto foi preenchido e lido,
   e Salvar foi acionado uma única vez. PDF de 28.688 bytes e 3 páginas,
   aberto por PyMuPDF sem reparo. Veja o
   [resultado do salvamento](resultado_salvamento_unico.md).

## Próximas etapas, sem execução nesta atualização

Inspeção somente de leitura da árvore concluída em 13/11/2026. Os nós possuem
nomes acessíveis e caminhos hierárquicos identificáveis. A seleção não foi
executada; recomenda-se testar a interface AccessibleSelection do pai, após
resolver o caminho exato. Veja o [diagnóstico](resultado_arvore.md).

Atualização: o teste autorizado de Operações Próprias executou uma única chamada
AccessibleSelection do pai e confirmou `selected` na folha. O visualizador não
forneceu confirmação pelo nome acessível pesquisado. A prova de seleção completa
permanece inconclusiva; nenhuma outra técnica foi tentada. Veja o
[resultado e alternativas](resultado_selecao_operacoes.md).

Critério atualizado pelo usuário: o estado `selected` confirma a seleção, pois
o PVA atualiza o visualizador automaticamente; título acessível não é exigido.
O novo teste confirmou a seleção de Operações Próprias e abriu Salvar por
descrição acessível. O processo Python ficou aguardando na fase posterior e
foi interrompido sem fechar o PVA. Nenhum PDF foi criado. A integração de
seleção com salvamento permanece pendente; veja o
[resultado do fluxo](resultado_fluxo_operacoes.md).

Investigação posterior com logs antes/depois e workers com timeout externo:
Processo A confirmou seleção, mas não encontrou o botão Salvar no visualizador
atual. Sem diálogo aberto, B não foi executado. A causa exata do bloqueio e a
eficácia da separação permanecem pendentes. Não houve novo salvamento. Veja a
[investigação](resultado_investigacao_modal.md).

- Receber os nomes exatos utilizados pelo usuário e as empresas de cada
  relatório para preparar o cadastro.
- Associar os caminhos observados aos relatórios do cadastro e testar a seleção
  de um único relatório mediante nova autorização específica.
- Avaliar a geração em lote e a execução com um clique após a prova de conceito
  e a revisão do cadastro. Nenhuma geração em lote está implementada.

Permanecem proibidas operações de alteração, exclusão, validação ou transmissão
de escriturações. A autorização de salvamento foi limitada ao PDF fictício
desta prova de conceito; outros salvamentos exigem nova autorização.
