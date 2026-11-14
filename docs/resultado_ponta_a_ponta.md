# Prova integrada aprovada — 13/11/2026, 11:52

Uma única execução coordenada localizou Operações Próprias na árvore, deu um
clique físico dinâmico na folha, aguardou Salvar, abriu o diálogo por clique
físico dinâmico, preencheu o caminho, confirmou uma vez e verificou o PDF.
Não houve intervenção manual entre as etapas.

## Resultado

- Caminho: Escrituração Fiscal → Relatórios de Registros Fiscais → Apuração
  do ICMS → Operações Próprias, resolvido por nomes exatos entre filhos.
- Um clique de ativação, com pais expandidos, visibilidade e foco conferidos.
- Salvar visível/habilitado, acionado uma única vez por click(simulate=True).
  Não foi usada ação acessível para abrir a modal.
- Conexão independente ao diálogo: isJavaWindow e obtenção de contexto true.
- Nome do arquivo preenchido e caminho absoluto confirmado por leitura.
- Destino inexistente antes do início e imediatamente antes da confirmação.
- Uma única confirmação de gravação; nenhum clique/salvamento repetido.
- Destino: saida/TESTE_FICTICIO/teste_integrado_operacoes_proprias.pdf.
- PDF: 3.539 bytes, 1 página, aberto por PyMuPDF sem senha ou reparo; página
  carregada. Arquivo estabilizado e diálogo fechado antes da verificação.
- Marcadores Operações Próprias e Apuração do ICMS encontrados no texto
  tratado somente em memória. Apenas flags booleanos foram registrados.
- Total: 7,9233 segundos. Todos os workers saíram com exit code 0, sem timeout.
- Nenhuma janela inesperada, configuração de acessibilidade preservada.

## Coordenação e tempos

| Etapa/worker | Tempo |
| --- | ---: |
| Localizar/ativar relatório, confirmar visualizador e encerrar worker | 2,3496 s |
| Clique físico no Salvar do visualizador | 0,014098 s |
| Worker de abertura de Salvar, incluindo espera pelo worker de gravação | 5,5295 s |
| Worker de gravação/verificação | 3,3771 s |
| Preencher caminho | 0,014215 s |
| Confirmar caminho por leitura | 0,002651 s |
| Confirmar Salvar uma vez | 0,077151 s |
| Aguardar gravação estável | 1,266061 s |
| Verificação estrutural PyMuPDF | 0,022977 s |
| Conferência de marcadores em memória | 0,026843 s |
| Execução coordenada total | 7,9233 s |

Tempos de workers sobrepõem-se: o processo que abre Salvar permaneceu vivo
enquanto o processo de gravação executava. O supervisor não dependeu da saída
do cliente abridor para iniciar a conexão ao diálogo.

Workers: relatório PID 22272; abertura de Salvar PID 13564; gravação PID 28924.
PVA PID 14432, HWND principal 1510638; diálogo HWND 3608396 nesta sessão.
Supervisor com limites externos: 30 s para ativação, 25 s para aparição da
modal, 35 s para gravação e 8 s para saída normal do abridor após gravação.
Nenhum limite foi atingido, nenhum processo foi morto.

## Reutilização e limites

scripts/poc_ponta_a_ponta.py coordena os workers aprovados de
ativar_operacoes_proprias.py, testar_salvar_fisico.py e concluir_pdf_fisico.py.
O destino fictício é específico desta prova, não altera o cadastro fixo de
nomes de produção. Uma trava persistente impede reutilizar esta autorização.

O botão Salvar já estava disponível antes do clique na folha nesta execução.
Sua presença isolada não demonstra atualização. Foram executados o clique
exato no caminho solicitado e a conferência posterior dos marcadores no PDF;
o teste anterior já comprovara a transição de ausente para disponível.

A conferência estrutural e os marcadores não validam a escrituração, valores
fiscais ou aparência integral do documento. Esta prova cobre somente um
relatório no ambiente atual. Não foram trocadas empresa/competência, gerados
outros relatórios, instaladas bibliotecas ou registrados conteúdos fiscais.
Não há execução em lote implementada.

Evidências: logs/ponta_a_ponta_20261113_115213/resultado.json e subpastas
relatorio, abrir_salvar e gravar. Logs imediatos registram antes/depois e
timestamps UTC; as subpastas incluem resultados, eventos e tempos por etapa.
