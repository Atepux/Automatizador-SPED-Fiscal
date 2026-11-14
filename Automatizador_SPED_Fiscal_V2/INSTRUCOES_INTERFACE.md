Consulte GUIA_DISTRIBUICAO.md para a interface e distribuição atuais (versão 2.3).

# Automatizador SPED Fiscal V2 — interface Windows

Abra `Iniciar.bat` nesta pasta. Ele usa o Python 32 bits configurado em
`config/programa.json`; não há executável EXE. Abrir a interface não faz
nenhum acesso ao PVA. Os componentes da V1 não são importados nem modificados.

## Cadastrar e importar

Na aba **Cadastro de Empresas**, use Cadastrar, Editar, Excluir ou Pesquisar.
O CNPJ é normalizado, validado pelos dois dígitos verificadores e não se repete.
O cadastro persistente fica em `dados/empresas.sqlite3`, criado na primeira
abertura da interface. Essa base contém os CNPJs completos necessários para
localizar escriturações e as configurações individuais; não é um log operacional.
Para transportar o cadastro com o programa fechado, preserve esse arquivo.

**Importar Empresas** aceita CSV, XLS e XLSM, sem cabeçalho, primeira linha já
com dados: coluna A = CNPJ, coluna B = nome. Linhas vazias são ignoradas.
CSV aceita UTF-8/BOM e Windows-1252, com ponto e vírgula, vírgula ou tabulação.
XLS usa xlrd; XLSM usa openpyxl em leitura de dados, sem executar macros.
As duas bibliotecas foram instaladas no Python configurado, com autorização.

CNPJ texto conserva zeros. CNPJ numérico só é aceito com 14 dígitos inteiros
ou com máscara explícita de 14 posições; sem essa evidência, não se adivinham
zeros e a linha é rejeitada. Duplicados não alteram nomes/configurações existentes.
O resultado informa importadas, existentes, rejeitadas e linha/motivo de cada
rejeição. O ícone (?) mostra o layout ao passar o mouse.

## Configurar os relatórios

Na aba **Configuração de Relatórios**, escolha a empresa. A árvore preserva
os caminhos Java reais. Clique na caixa de uma folha para marcar/desmarcar;
as categorias podem ser expandidas. A seleção só alterna ao clicar no ícone da
caixa; clicar no nome apenas escolhe a linha para edição. Selecione a folha,
dê duplo clique no nome do PDF na tabela, edite e confirme com Enter. Depois clique Salvar configurações.
Todos os relatórios selecionados são obrigatórios; não existe opção Opcional.

Nomes selecionados não podem se repetir na mesma empresa. A alteração de uma
empresa não altera as demais. Ao trocar de empresa com mudanças pendentes,
a interface pergunta antes de descartá-las.

**Selecionar Padrão** marca exatamente Entradas, Saídas, Próprias, ST e Recibo,
desmarcando os demais somente na empresa selecionada; conserva nomes personalizados.
Todas as empresas novas recebem esse padrão automaticamente.

O catálogo inicial reúne 29 folhas reais do diagnóstico anterior: oito
relatórios aprovados, outros itens para o fluxo genérico e dois itens especiais
bloqueados (Dados da Escrituração e Assinatura). DIFAL não integra o catálogo
executável. O nome original do PVA permanece na árvore. Caracteres proibidos
em nomes de arquivo Windows são substituídos no nome inicial de novos PDFs;
o nome original do nó não é alterado.

**Atualizar árvore do PVA** faz somente leitura Java, sem selecionar relatórios,
expandir nós ou salvar PDFs. Requer uma escrituração já aberta manualmente,
com a árvore acessível e sem diálogos; não abre uma escrituração só para isso.
Itens descobertos ficam disponíveis, desmarcados e com o nome inicial do PDF.
Não se inventam caminhos. Interações especiais não são confirmadas automaticamente.
Relatórios adicionais ainda precisam de validação real individual; se faltarem
os controles genéricos de visualização/salvamento, o processamento interrompe.

## Processar empresas — aguarda teste real de troca

Antes do primeiro uso multiempresas, validar o fechamento e a troca de duas
empresas reais, conforme autorização pendente. A nova interface e a coordenação
multiempresas foram testadas somente offline nesta etapa.

1. Abra o PVA e deixe-o **sem escrituração ativa e sem diálogos**.
2. Na aba Processamento, selecione as empresas, informe a competência (a barra / é preenchida automaticamente) e escolha a
   pasta principal. Salve antes qualquer configuração pendente.
3. Clique Iniciar processamento. Não use o mouse/teclado no PVA durante a execução:
   os cliques físicos usam limites Java calculados dinamicamente.
4. Acompanhe empresa, relatório, PDFs, progresso, status e tempo na interface.
5. Parar solicita interrupção no próximo ponto seguro, após o salvamento em
   andamento; não mata o PVA ou interrompe um diálogo no meio da operação.

O fluxo exige CNPJ + primeiro e último dia do mês, correspondência única,
seleção confirmada e identificação pelo rodapé. Nome e posição da empresa
não são usados para escolher a escrituração. Duplicidade não resolvida bloqueia.
Nenhuma empresa é fechada automaticamente só porque já estava aberta no início.

Executa somente os relatórios selecionados, na ordem aprovada dos oito conhecidos.
Adicionais genéricos seguem depois dos conhecidos, em ordem hierárquica.
Próprias/ST mantêm subrelatórios obrigatórios; outros não alteram essa caixa.
Controle de Créditos Fiscais também é obrigatório quando selecionado. Sua ausência
interrompe o processamento, assim como a ausência de qualquer selecionado. Recibo
mantém até 5 segundos e os cliques mantêm a espera mínima aprovada de 2 segundos.

Após todos os relatórios da empresa, a identidade é reconfirmada; Fechar é
acionado pelo comando normal, uma única vez, sem confirmar avisos. Abrir deve
voltar a ficar habilitado e o estado vazio deve ser comprovado antes da próxima.
Indicador de alteração, aviso, falha ou fechamento não confirmado interrompem.
O PVA nunca é encerrado. Após falha inesperada, a escrituração é preservada
para revisão; não se fecha por conta própria nem se repetem cliques.

## Pastas e registros

```text
Pasta principal/
  2026-10/
    Empresa A - CNPJ/
      nomes exatos e personalizados.pdf
    Empresa B - CNPJ/
      nomes exatos e personalizados.pdf
```

Os nomes das pastas são sanitizados e o CNPJ evita colisões entre nomes iguais.
Antes de acessar o PVA, a existência de qualquer PDF do lote bloqueia a execução.
A publicação final usa criação exclusiva, sem sobrescrita, inclusive se um
arquivo aparecer durante o processamento. PyMuPDF valida abertura, páginas e
estrutura antes da publicação. Não existe envio para serviços externos.

Para não levar CNPJ completo aos logs dos auxiliares aprovados, a geração
utiliza uma área local `temporarios/<execução>/` com nomes técnicos. Depois de
validado, o PDF é copiado exclusivamente ao nome final e o temporário é removido.
Em falha, pode permanecer um PDF temporário local para revisão; ele não é um log.

`logs/multi_<execução>/` contém resumos JSON/CSV consolidados, resumos individuais
em `empresa_001/`, `empresa_002/` e registros técnicos. Esses registros usam
identificadores e dados mascarados, sem CNPJ completo ou texto fiscal extraído.
A interface exibe os CNPJs para permitir a escolha correta; isso não os grava
nos logs operacionais.

Travas impedem execução simultânea pelas entradas V2. Após reiniciar a interface,
travas de processos comprovadamente encerrados só são arquivadas se não houver
auxiliares V2 restantes. Travas ativas, desconhecidas ou com auxiliares são
preservadas; nenhum processo é encerrado e nenhum clique é repetido.
A interface continua responsiva: automação roda em thread, auxiliares com
timeout e atualizações por fila, somente a thread principal modifica o Tkinter.

## Validação desta entrega

61 testes offline aprovados, incluindo cadastro e persistência SQLite, padrão
exato, isolamento de configurações, importação, validação de nomes/CNPJ,
simulação de duas empresas, PDFs de teste locais, falhas, parada e fechamento.
A interface foi construída em teste Tkinter sem acessar o PVA. A leitura XLS
teve o adaptador exercitado com células simuladas e arquivo inválido; CSV e
XLSM também tiveram arquivos de teste reais. Não foram importados dados reais
de empresas nem executados relatórios reais nesta etapa.

Ainda dependem de teste autorizado no PVA: fechamento normal sem alterações,
avisos de pendências, abertura da segunda empresa, lote completo pela nova UI,
atualização da árvore e comportamento dos relatórios adicionais genéricos.
