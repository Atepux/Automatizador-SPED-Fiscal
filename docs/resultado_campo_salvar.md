# Campo Nome do arquivo — 13/11/2026

Teste realizado no processo PVA 14432, dialogo HWND 658798, classe SunAwtDialog.
Conexao pyjab bem-sucedida com a mesma bridge de 32 bits da prova anterior.

Controles identificados por nome e papel acessivel:

- Salvar em: — combo box.
- Nome do arquivo: — text, enabled, editable, single line, visible, showing.
- Arquivos do tipo: — combo box; conteudo da selecao nao foi coletado.
- Salvar — push button.
- Cancelar — push button.

O campo de nome foi identificado univocamente pelo papel text e nome acessivel
Nome do arquivo:. Caminho observado: [0,1,0,0,2,2,2,1]. Os indices sao apenas
evidencia desta sessao; a selecao do script depende de nome e papel.

Foi chamada setTextContents da bridge carregada pelo pyjab e o texto foi lido
de volta pela propriedade text do elemento. O conteudo retornado coincidiu
integralmente com:

`C:\Users\contabil02\Downloads\Projetos\Automatizador Sped Fiscal\saida\TESTE_FICTICIO\relatorio_teste.pdf`

O caminho completo, incluindo espacos e extensao .pdf, pode ser inserido
diretamente no campo. Isso comprova a entrada e leitura do texto, mas nao a
aceitacao final do destino pelo JFileChooser nem a gravacao do PDF.
A pasta ficticia nao foi criada pelo teste.

Nenhum clique, coordenada fixa ou tecla foi utilizado. A janela permaneceu
aberta com o caminho ficticio preenchido. Salvar e Cancelar nao foram acionados.
O arquivo de destino nao existia antes e continuou inexistente depois.
A configuracao de acessibilidade permaneceu identica. Nenhuma biblioteca foi
instalada; nenhum conteudo anterior do campo ou lista de arquivos foi registrado.

Evidencia: logs/campo_salvar_20261113_102815.json.
