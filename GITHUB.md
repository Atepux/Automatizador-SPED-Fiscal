# Código-fonte e dados locais

O repositório contém fontes, testes offline, configurações genéricas e documentação.
As pastas V1 e V2 são preservadas; nenhum programa precisa ser executado para
versionar o projeto. A V1 é uma versão histórica e não deve ser modificada ao
desenvolver a V2.

## Fora do Git

Cadastros SQLite, escriturações, PDFs, planilhas, resultados de testes manuais,
logs, arquivos temporários, ambientes virtuais, caches, executáveis, DLLs,
pacotes de fornecedores e compilações permanecem apenas no computador.
Credenciais, chaves e arquivos de ambiente também são excluídos.

`config/diagnostico.toml` e `config/programa.json`, inclusive nas versões V1/V2,
são configurações particulares da máquina e não são publicados. Os modelos
correspondentes ficam em `config/exemplos/provas`, `config/exemplos/V1` e
`config/exemplos/V2`. Após clonar, copie os modelos necessários para a pasta
`config` da versão escolhida, somente se o arquivo de destino ainda não existir.
Ajuste localmente o caminho do Python de 32 bits. O valor vazio de `bridge_dll`
permite descoberta automática da ponte Java, conforme o ambiente preparado.

As configurações de catálogo e nomes padrão de relatórios são genéricas e
podem ser versionadas. Não coloque empresas ou critérios reais de seleção
nesses arquivos. O cadastro permanente deve permanecer em SQLite fora do Git.

## Integridade das rotinas

O projeto confere hashes de versões aprovadas. Por isso `.gitattributes`
preserva os bytes e as quebras de linha dos arquivos, evitando conversões
automáticas que invalidariam essas conferências.

## Antes de publicar novas alterações

Revise `git status`, `git diff --cached` e a lista de arquivos adicionados.
Não use inclusão forçada para arquivos ignorados. Não inclua cadastros, PDFs,
escriturações, configurações locais ou credenciais, mesmo em repositório privado.
Consulte o histórico remoto antes de enviar e nunca use `push --force`.
