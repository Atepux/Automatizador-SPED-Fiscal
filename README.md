# Automatizador SPED Fiscal

**Automação inteligente de relatórios do SPED Fiscal (EFD ICMS/IPI)**

![Python](https://img.shields.io/badge/Python-Automação-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-Desktop-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-orange?style=for-the-badge)
![Versão](https://img.shields.io/badge/Versão-V2-blue?style=for-the-badge)

---

## Sobre o projeto

O **Automatizador SPED Fiscal** é uma ferramenta desenvolvida em Python para automatizar a extração de relatórios do Programa Validador e Assinador (PVA) da EFD ICMS/IPI.

O projeto nasceu da necessidade de reduzir tarefas manuais e repetitivas na rotina contábil e fiscal, especialmente em ambientes que exigem a geração de relatórios de múltiplas empresas e períodos de apuração.

A ferramenta automatiza a interação com o PVA, permitindo executar operações de forma padronizada, reduzindo o tempo de processamento e a necessidade de intervenção manual.

### Objetivos

- Reduzir o tempo gasto na emissão de relatórios fiscais.
- Automatizar tarefas repetitivas dentro do PVA.
- Facilitar o processamento de múltiplas escriturações.
- Padronizar a geração de relatórios em PDF.
- Minimizar erros operacionais decorrentes de processos manuais.
- Tornar a rotina fiscal mais eficiente e organizada.

---

## Funcionalidades

### Automação do PVA

- Interação automatizada com a interface do programa.
- Seleção e abertura de escriturações fiscais.
- Identificação da escrituração ativa pelo rodapé do PVA.
- Conferência de CNPJ e período de apuração.
- Navegação pelas opções de relatórios.
- Fechamento da escrituração para processamento da próxima.

### Geração de relatórios

Automatização da emissão de relatórios fiscais, incluindo:

| Relatório | Descrição |
|---|---|
| Entradas | Operações de entrada de mercadorias |
| Saídas | Operações de saída de mercadorias |
| Operações Próprias | Apuração das operações próprias |
| Operações ST | Apuração da substituição tributária |
| Recibo | Recibo da escrituração |

A disponibilidade dos relatórios depende da escrituração e das opções oferecidas pelo PVA.

### Seleção de relatórios

O projeto contempla a configuração dos relatórios a serem processados, incluindo uma seleção padrão para agilizar a rotina.

### Processamento sequencial

O fluxo de automação foi estruturado para permitir o processamento de diferentes empresas e períodos, utilizando uma mesma instância do PVA.

*Funcionalidade em desenvolvimento e validação na versão V2.*

---

## Como funciona

O funcionamento do automatizador segue um fluxo de operações dentro do PVA.

**1. Inicialização**

O automatizador inicia a interação com o PVA, preparando o ambiente para a seleção da escrituração.

**2. Seleção da escrituração**

A empresa e o período desejados são selecionados na lista de escriturações disponíveis.

**3. Confirmação**

Após a abertura, o sistema utiliza as informações apresentadas no rodapé do PVA, especialmente o CNPJ e o período, para confirmar que a escrituração correta está ativa.

**4. Emissão dos relatórios**

O automatizador acessa as opções correspondentes, configura os relatórios e realiza a geração dos arquivos PDF.

**5. Encerramento da escrituração**

Ao finalizar o processamento, a escrituração é fechada, mantendo o PVA aberto.

**6. Próxima escrituração**

O fluxo é repetido para a próxima empresa ou período, conforme a configuração da execução.

### Fluxo resumido

```text
INÍCIO
  |
  v
Inicializar PVA
  |
  v
Selecionar escrituração
  |
  v
Confirmar CNPJ e período
  |
  v
Selecionar relatórios
  |
  v
Gerar arquivos PDF
  |
  v
Fechar escrituração
  |
  v
Existem outras escriturações?
  |
  +--- SIM ---> Próxima escrituração
  |
  +--- NÃO ---> Finalizar
```

---

## Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal de desenvolvimento |
| Automação de interface | Interação com o PVA |
| Git | Controle de versões |
| GitHub | Armazenamento e gerenciamento do código |
| PyInstaller | Distribuição em formato executável Windows |

As bibliotecas específicas e suas versões devem ser consultadas nos arquivos de dependências do projeto.

---

## Instalação e utilização

### Requisitos

- Sistema operacional Windows.
- PVA da EFD ICMS/IPI instalado e configurado.
- Escriturações previamente disponíveis no PVA.
- Ambiente compatível com a versão distribuída do automatizador.

### Utilização

1. Obtenha a versão compatível do programa.
2. Prepare o PVA e as escriturações que serão processadas.
3. Inicie o automatizador.
4. Configure as empresas, períodos e relatórios desejados, conforme os recursos disponíveis na versão.
5. Execute a automação.
6. Confira os arquivos PDF gerados.

**Importante:** a ferramenta não substitui a conferência técnica e fiscal dos relatórios emitidos.

---

## Estrutura do projeto

A organização dos arquivos pode incluir:

```text
Automatizador-SPED-Fiscal/
|
|-- README.md
|-- .gitignore
|
|-- [Código-fonte Python]
|-- [Configurações]
|-- [Scripts de compilação]
|
|-- [Documentação]
```

*A estrutura definitiva deve refletir os arquivos existentes no repositório.*

Arquivos temporários, ambientes virtuais, executáveis compilados e relatórios fiscais não devem ser incluídos desnecessariamente no histórico Git.

---

## Versões e atualizações

O desenvolvimento é organizado por versões, permitindo acompanhar melhorias, correções e alterações de funcionamento.

| Versão | Descrição |
|---|---|
| V1 | Desenvolvimento inicial da automação |
| V2 | Evolução do fluxo de seleção, confirmação e geração de relatórios |
| Futuras | Melhorias, otimizações e novas funcionalidades |

As versões compiladas poderão ser disponibilizadas na seção **Releases** do repositório, conforme a política de distribuição adotada.

---

## Segurança e confidencialidade

Este projeto é destinado à automação de rotinas que podem envolver informações fiscais e cadastrais de empresas.

Por esse motivo:

- Dados fiscais reais não devem ser publicados no repositório.
- Arquivos contendo credenciais devem permanecer protegidos.
- Relatórios gerados devem ser armazenados em locais apropriados.
- O acesso ao código e às versões distribuídas deve respeitar as permissões estabelecidas.
- A execução deve ocorrer em ambientes autorizados.

---

## Status do desenvolvimento

**Em desenvolvimento — Versão 2**

O projeto está em processo de evolução, com foco na estabilidade da automação, no processamento de múltiplas escriturações e na confiabilidade da geração de relatórios.

As funcionalidades podem sofrer alterações durante o desenvolvimento.

---

## Finalidade

O Automatizador SPED Fiscal foi desenvolvido para apoiar a produtividade em rotinas contábeis e fiscais, utilizando automação para transformar processos operacionais repetitivos em fluxos mais eficientes, organizados e padronizados.

---

**Automatizador SPED Fiscal**

*Automação aplicada à eficiência contábil e fiscal.*
