# Cadastro recuperado — 13/11/2026

config/poc_tres_relatorios.json mantém o caminho de arquivo por compatibilidade,
mas agora contém oito entradas com nomes definidos, sendo uma opcional.
Os três itens anteriores foram preservados. Não houve acesso ao PVA,
execução ou salvamento nesta atualização.

Todos os oito caminhos foram conferidos literalmente contra o diagnóstico
logs/arvore_20261113_103518.json. Nenhum caminho foi inventado.

Sob Escrituração Fiscal:

| ID | Caminho abaixo da raiz | Nome exato de saída |
| --- | --- | --- |
| operacoes_proprias | Relatórios de Registros Fiscais → Apuração do ICMS → Operações Próprias | Registros Fiscais da Apuração do ICMS_Operações Próprias.pdf |
| operacoes_st | Relatórios de Registros Fiscais → Apuração do ICMS → Substituição Tributária | Registros Fiscais da Apuração do ICMS_Operações ST.pdf |
| documentos_entradas | Relatórios de Registros Fiscais → Documentos → Entradas de Mercadorias e Aquisição de Serviços | Registros Fiscais dos documentos de entradas de mercadorias e aquisição de serviços.pdf |
| pagamentos_eletronicos | Outras Informações → Operações com Instrumentos de Pagamentos Eletrônicos | Operações com instrumentos de Pagamentos Eletrônicos.pdf |
| recibo | Recibo de Transmissão | Recibo.pdf |
| ciap | ICMS - Ativo Permanente - CIAP | Registros Fiscais de Controle de Créditos de ICMS do Ativo Permanente - CIAP.pdf |
| documentos_saidas | Relatórios de Registros Fiscais → Documentos → Saídas de Mercadorias e Prestação de Serviços | Registros Fiscais dos documentos de saídas de mercadorias e prestação de serviços.pdf |
| controle_creditos_fiscais | Outras Informações → Controle de Créditos Fiscais - ICMS | Registro de Controle de Créditos Fiscais.pdf |

A caixa de subrelatórios é obrigatória somente para Operações Próprias/ST.
Nos demais, false significa não alterar a caixa, não significa desmarcá-la.
DIFAL RJ/SP não está presente no cadastro de geração.

O opcional tem opcional=true e quando_indisponivel=ignorar_sem_interromper_lote.
O nome foi confirmado pelo usuário e habilitado=true. Continua opcional e não
altera a checkbox de subrelatórios. Essa política está registrada no cadastro; a execução
do lote ampliado não foi implementada ou testada nesta etapa. O script histórico
de três relatórios permanece limitado explicitamente aos seus três IDs.

Marcadores de conteúdo dos itens novos são candidatos baseados nos rótulos
observados; ainda não foram validados em PDFs desses relatórios. Não são nomes
de arquivo nem condição de cadastro incompleto de caminhos.

Conferências offline: oito caminhos existentes no diagnóstico, oito nomes
distintos, apenas os dois flags obrigatórios de subrelatórios, nenhuma entrada
DIFAL e nenhum nome de saída pendente. Não foram atribuídas empresas aos
novos itens nem presumida sua aplicabilidade a todas as empresas.
