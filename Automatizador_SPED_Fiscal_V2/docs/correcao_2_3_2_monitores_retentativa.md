# Correção 2.3.2 — monitores e nova tentativa

Os dois registros enviados comprovaram a abertura correta, seleção única e
identificação pelo rodapé. O primeiro relatório interrompeu com bounds_invalidos,
zero cliques, após receber x=-1859, y=176, largura=245 e altura=18. A validação
antiga rejeitava qualquer posição negativa, embora monitores à esquerda ou
acima do principal usem essas coordenadas normalmente.

Agora a validação aceita posições negativas finitas, exige dimensões positivas
e verifica o ponto físico na área virtual real dos monitores. A conferência da
janela sob o ponto calculado pelo Java continua obrigatória. Não foram adotadas
coordenadas fixas e não há repetição de cliques em caso de falha.

Os auxiliares são acompanhados pelos próprios objetos Popen criados na execução,
incluindo aqueles da geração de PDF. Encerrar com erro não equivale a continuar
executando: as travas pertencentes à própria sessão são liberadas depois de
comprovar o término de todos os auxiliares. Travas de outros donos não são
apagadas; nenhum processo ativo é encerrado por essa limpeza.

A interface só recebe a notificação de fim depois da limpeza e apresenta
Tentar novamente. Caso um auxiliar esteja ativo, a nova tentativa apenas
informa a pendência e não executa ações no PVA. Quando ele terminar, a mesma
sessão pode verificar novamente e prosseguir.

Uma nova tentativa pode reutilizar a primeira escrituração solicitada se CNPJ
e período forem confirmados pelo rodapé. Uma escrituração diferente ou diálogo
aberto continuam impedindo a execução. PDFs existentes permanecem protegidos;
se o lote anterior gerou arquivos, é necessário escolher outro destino.

78 testes offline aprovados. O executável 2.3.2 passou em perfil isolado,
incluindo simulação de falha seguida de nova tentativa com a mesma escrituração
aberta, duas empresas e 16 PDFs sintéticos. A V1 foi preservada. Nenhum lote,
clique, fechamento de escrituração ou alteração nas travas/cadastro reais do
usuário foi executado nesta correção.
