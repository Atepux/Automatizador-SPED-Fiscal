# Janela de seleção identificada — 13/11/2026, 15:44

Procedimento autorizado: Fechar atual se necessário, Abrir lista e inspecionar.
Não selecionar linha, não confirmar abertura, não gerar relatórios/PDFs.

## Comandos normais do PVA

O menu Escrituração Fiscal foi localizado dentro da barra de menus, sem
confundir Fechar do relatório com Fechar da escrituração. No início desta
execução, Fechar da escrituração já estava desabilitado; não foi acionado.
O PVA já estava sem escrituração aberta. Abrir estava habilitado.

Foram executados somente a abertura do menu e o clique no comando Abrir,
por limites Java dinâmicos, sem posições fixas. Não surgiu aviso de alteração
pendente. O ramo efetivo de fechamento de uma escrituração não foi testado
nesta sessão; continua condicionado à ausência de avisos/alterações pendentes.
Nenhum aviso desconhecido foi confirmado.

## Controles confirmados

- Janela Abrir Escrituração, classe SunAwtDialog, HWND 134740 nesta sessão,
  mesmo PID 30852 do PVA. Modal, reconhecida por pyjab.
- Tabela Java table, habilitada, visível, focável e com AccessibleSelection.
  Nesta sessão: 62 linhas e 9 colunas. Os registros não foram lidos.
- Colunas obtidas diretamente do cabeçalho via Java Access Bridge:
  Contribuinte; UF; CPF/CNPJ; Inscrição Estadual; Data Inicial; Data Final;
  Descritor; Finalidade do Arquivo; Estado.
- Botão Ok, push button, enabled/visible/showing, ação acessível clicar.
- Botão Cancelar, push button, enabled/visible/showing, ação acessível clicar.
- Área de texto de instruções não editável. Nenhum campo editável dedicado
  a pesquisa/filtro foi identificado nesta inspeção. Não inventar atalho ou
  comportamento de filtro por digitação sem teste autorizado.

Os cabeçalhos são metadados estáticos. Para identificar Finalidade do Arquivo,
o texto do cabeçalho precisou ser normalizado de sua apresentação HTML. Não
houve leitura de células de dados para obter os nomes das colunas.

## Proposta para localizar CNPJ e competência

1. Partir de Escrituração Fiscal → Abrir quando habilitado; se houver uma
   escrituração aberta, usar Fechar somente na etapa autorizada e interromper
   diante de aviso pendente/inesperado, sem confirmar.
2. Confirmar título/classe/PID da janela e localizar a tabela dinamicamente.
3. Mapear colunas pelos nomes de cabeçalho em cada execução, sem assumir ordem
   fixa, posições de linhas ou índices do diagnóstico.
4. Ler as células de CPF/CNPJ, Data Inicial e Data Final em memória e procurar
   igualdade com o alvo configurado. Não selecionar pelo nome Contribuinte.
5. Competência deve ser convertida em intervalo de datas esperado, comparando
   início E fim. A forma concreta dos valores nas células e sua normalização
   ainda precisam ser verificadas em leitura autorizada de dados-alvo.
6. Exigir uma única correspondência. Se houver duplicatas, usar IE, finalidade
   e descritor explicitamente configurados; não escolher automaticamente a
   primeira. Falta ou ambiguidade interrompem.
7. Sob nova autorização, testar seleção da linha e confirmar leitura de seus
   identificadores antes de acionar Ok uma única vez. Não usar clique duplo,
   pois pode abrir diretamente a escrituração e dificultar a pré-confirmação.
8. Depois da abertura, conferir a identidade ativa por fonte independente
   antes de chamar o gerador aprovado. Essa fonte ainda não foi mapeada: nesta
   etapa nenhuma escrituração foi aberta. Seleção não equivale a abertura.

Sem campo de pesquisa dedicado confirmado, a proposta usa acesso estruturado
à tabela Java. Nenhuma escrita em filtro, seleção de linha, tecla ou Ok foi
executado para testar essa proposta. Valores fiscais devem ser comparados só
em memória; logs conterão aliases/resultados booleanos, não CNPJs completos.

## Estado final

A janela Abrir Escrituração permaneceu aberta, sem confirmação. Não há outra
escrituração aberta automaticamente, relatórios gerados ou PDFs salvos. Os
processos auxiliares encerraram normalmente, sem timeout. V1 não modificada.

Evidências: logs/lista_escrituracoes_20261113_154421/resumo.json,
fechar.resultado.json, abrir.resultado.json, interface.json e
colunas_sanitizadas.json. O cadastro de controles está em
config/controles_selecao.json. Não contém CNPJ ou dados de empresas.
