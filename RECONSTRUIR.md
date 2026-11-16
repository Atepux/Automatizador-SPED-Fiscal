# Reconstruir o Automatizador SPED Fiscal

## Base publicada
O código da aplicação, scripts, testes, configurações técnicas de base, documentação e `empacotamento/construir.py` estão versionados. A publicação contém os fontes do projeto, não dados de empresas, escriturações fiscais ou relatórios privados. Não copie arquivos de `dados/`, `saida/`, `logs/`, perfis locais ou credenciais para um commit.

## Ambiente registrado para a versão 2.3.2
A versão publicada foi construída no Windows com CPython 3.14 x86 (32 bits). Use um ambiente isolado, confirme arquitetura por `struct.calcsize("P") * 8` e não instale dependências no Python global.

Dependências diretas utilizadas pelo script de build:
- PyInstaller 6.22.3
- PyMuPDF 1.26.7 (MuPDF 1.26.12 para build a partir de fontes)
- pywin32 312
- openpyxl 3.1.5
- xlrd 2.0.2
- pyjab 1.12.0 (snapshot adaptado incluído em `third_party/pyjab-1.12.0-fontes.zip`)

As dependências transitivas devem ser resolvidas e registradas no ambiente de build. `requirements-build.txt` fixa os requisitos diretos conhecidos. O `construir.py` também coleta metadados/licenças de `et_xmlfile`, dependência transitiva de openpyxl.

## Preparação das fontes de terceiros
O build atual usa os arquivos em `empacotamento/fornecedores`, que não são versionados:
- `pymupdf-1.26.7.tar.gz`: sdist oficial do PyPI, pacote PyMuPDF 1.26.7.
- `mupdf-1.26.12-source.tar.gz`: fonte oficial MuPDF 1.26.12.

Obtenha os arquivos nas fontes oficiais indicadas em `empacotamento/construir.py` e no registro de reprodução do release. Verifique metadados, hashes publicados pelo fornecedor e licenças antes de usar. Não coloque arquivos de clientes ou PDFs fiscais nessas pastas. O PyMuPDF/MuPDF está sob AGPL ou licença comercial Artifex; a distribuição do aplicativo precisa cumprir a licença aplicável.

Para pyjab, instale a versão 1.12.0 para disponibilizar metadados da distribuição e sobreponha o conteúdo do snapshot licenciado incluído, preservando os arquivos `dist-info` instalados. O ZIP contém os módulos Python; a licença MIT e copyright estão em `third_party/pyjab-LICENSE.txt`.

## Compilar e validar
1. Crie um venv com a mesma arquitetura e versão de Python anotadas acima.
2. Instale `requirements-build.txt` e pyjab 1.12.0; aplique o snapshot fonte de pyjab.
3. Coloque os dois arquivos oficiais PyMuPDF/MuPDF em `Automatizador_SPED_Fiscal_V2/empacotamento/fornecedores/`.
4. No diretório `Automatizador_SPED_Fiscal_V2`, execute `python empacotamento/construir.py`.
5. Para testes unitários: `python -m unittest discover -s tests -q`.
6. Revise o relatório do build e o hash do executável. A compilação não deve acessar arquivos fiscais do usuário.

Os requisitos oficiais do PVA são necessários para operar as funções que dependem dele, mas não para reconstruir o executável. Java e PVA são requisitos de uso específicos e não são fornecidos por este roteiro.

## O que o GitHub não contém
Os sdists grandes de PyMuPDF/MuPDF não foram espelhados no repositório. Um build limpo depende de obtê-los das fontes oficiais, confirmar as versões e cumprir AGPL/licença comercial aplicável. Logo, o clone contém toda a base de código do aplicativo e scripts, mas uma reconstrução isolada, sem rede nem arquivos externos, ainda não é possível.
