# Confirmação pelo rodapé — 13/11/2026

Leitura somente Java na escrituração já aberta. Nenhum clique, troca de
escrituração, relatório ou PDF neste teste. V1 não modificada.

O rodapé foi lido em um controle Java `label`, caminho observado
`[0,1,0,0,0,1]`, contendo CNPJ e as duas datas no mesmo texto. A comparação
em memória confirmou correspondência exata com os critérios autorizados no
teste anterior. Nenhum valor fiscal foi persistido. Abertura aprovada.

Evidência: `logs/rodape_20261113_155726/resultado.json`.

`scripts/rodape_escrituracao.py` descobre o label dinamicamente, por papel,
visibilidade, localização relativa inferior e presença dos campos de identidade.
Não usa o caminho observado como índice fixo nem executa interações.

A rotina de seleção agora aguarda até 10 segundos pela ausência de diálogos,
pelo desaparecimento da janela de seleção e pelo retorno da janela principal
visível e habilitada. Diálogos transitórios não causam falha imediata; diálogos
persistentes causam timeout, sem interação. Em seguida, lê e compara o rodapé.
Falha de leitura, divergência, modal ou timeout bloqueia a liberação por identidade.

O indicador `geracao_liberada_por_identidade` informa somente que a identidade
foi confirmada naquela verificação. Não inicia geração, não é uma autorização
para futuros lotes e não deve ser reutilizado após mudança da interface.

Treze testes offline passaram, incluindo correspondência, divergência e
ausência de identidade, modal transitória e modal persistente. O novo fluxo
de espera após Ok não foi novamente executado no PVA nesta etapa.
