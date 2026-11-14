# Automatizador SPED Fiscal V2 — versão 2.3.2

## Para usar em outro computador

1. Envie **Automatizador_SPED_Fiscal_V2_2.3.2.exe**. O arquivo não contém suas empresas,
   configurações particulares, escriturações ou PDFs.
2. Abra o arquivo em um computador Windows 10/11 com o PVA EFD ICMS/IPI instalado.
   Não é necessário instalar Python, openpyxl, xlrd ou bibliotecas manualmente.
3. No primeiro uso, se solicitado, clique **Preparar acesso automaticamente**.
   É necessária internet para baixar o componente oficial de comunicação Java
   (cerca de 38 MB). Ele fica privado para esse usuário, sem trocar o Java do PVA
   nem modificar o PATH do Windows.
4. Se o programa informar que habilitou a comunicação, feche e abra o PVA uma vez.
5. Cadastre ou importe as empresas, escolha os relatórios e deixe o PVA aberto,
   sem escrituração ativa, antes de iniciar o processamento.

O PVA não é incluído no arquivo. A integração real foi aprovada no ambiente de
desenvolvimento; versões diferentes de PVA/Windows e políticas restritivas de
outros computadores precisam ser verificadas no primeiro uso. Nenhum programa
pode garantir funcionamento universal independentemente do ambiente.

## Seu cadastro atual

Para continuar com suas empresas e nomes personalizados, use **Fazer backup**
na versão em Python e depois **Restaurar cadastro** na versão EXE. Também pode
selecionar diretamente o arquivo `dados/empresas.sqlite3` da pasta antiga.
O cadastro atual é copiado antes da restauração e os PDFs não são tocados.
Não envie esse backup a terceiros se não quiser compartilhar suas empresas.

No EXE, cadastro e registros ficam em:

`%LOCALAPPDATA%\AutomatizadorSPEDFiscal\V2`

Atualizar ou enviar o EXE não inclui nem apaga o cadastro dessa pasta.
Na versão em Python, o cadastro continua na própria pasta do projeto.

## Interface

- Navegação lateral em azul: Processamento, Empresas e Relatórios.
- Tabelas com linhas alternadas, categorias destacadas e maior espaçamento.
- Marcar/desmarcar somente ao clicar na caixa.
- Competência com `/` automática.
- Para mudar o PDF, dê **duplo clique no nome na tabela**, digite e pressione
  **Enter**. **Esc** cancela. Depois clique **Salvar configurações**.
- Todos os relatórios selecionados são obrigatórios; nenhum arquivo é sobrescrito.

**Atualizar árvore do PVA** serve para descobrir novos relatórios, não para o
processamento mensal normal. Requer uma escrituração aberta e sem diálogos.
Expande somente categorias recolhidas para ler seus filhos pela Java Access
Bridge; não ativa relatórios nem gera PDFs. O catálogo anterior é preservado
se não for possível ler a árvore com segurança.

## Distribuição e código-fonte

O aplicativo é distribuído sob **GNU AGPL v3**, conforme autorização do titular,
para manter o uso da versão comunitária do PyMuPDF. O botão **Código-fonte e
licenças** abre os fontes do aplicativo, do PyMuPDF/MuPDF e os avisos de terceiros
que acompanham o próprio executável. Nenhum dado fiscal acompanha esses fontes.

O componente Java é obtido diretamente do fornecedor Azul, em pacote OpenJDK
com verificação SHA-256 e preservação dos avisos de licença. A preparação só
altera a configuração de acessibilidade do usuário, com backup do arquivo
preexistente; outros recursos de acessibilidade são preservados.

## Compilação a partir dos fontes

Use Windows, Python 3.14 de 32 bits, PyInstaller 6.22.3, PyMuPDF 1.26.7,
pywin32 312, openpyxl 3.1.5 e xlrd 2.0.2. O pyjab 1.12.0 usado nesta entrega
tem seus fontes exatos incluídos: extraia seu ZIP como pacote `pyjab` no projeto.
Instale suas dependências declaradas (veja o arquivo REPRODUZIR.txt em FONTES).

O script `empacotamento/construir.py` monta o runtime, faz autoteste offline e
gera o iniciador único. Os arquivos originais de fornecedores usados para
montar o pacote de fontes podem ser obtidos nos endereços do REPRODUZIR.txt.
A V1 não é necessária para executar ou compilar a V2.

Não foram executados novos lotes fiscais para testar a distribuição. O autoteste
do EXE verifica telas, bibliotecas, PDF sintético e processos auxiliares; a
automação real deve ser conferida no computador de destino.

## Correção 2.3.2

Corrige a localização das configurações nos módulos importados dentro do EXE e
a ativação verificada da janela do PVA. O autoteste inclui a conferência dos
recursos dos nove módulos operacionais e simulação offline de duas empresas
com 16 PDFs, além da construção da interface e comunicação com auxiliares.
Nenhum novo lote real no PVA foi executado para validar esta correção.
Feche a versão anterior antes de abrir a nova; o cadastro local é preservado.

## Monitores e nova tentativa (2.3.2)

Aceita monitores à esquerda ou acima do principal, cujas coordenadas podem ser
negativas. O ponto continua sendo calculado pelo Java e conferido na área real
dos monitores e na janela do PVA antes de qualquer clique.

Após falha, as travas da própria execução são liberadas quando todos os auxiliares
terminam. O botão Tentar novamente não exige reiniciar o programa. Se a primeira
empresa/competência solicitada já estiver aberta e seu rodapé corresponder, ela
é reutilizada. Outra escrituração ou um diálogo aberto bloqueiam com mensagem
específica; não são fechados automaticamente. PDFs existentes continuam protegidos.
