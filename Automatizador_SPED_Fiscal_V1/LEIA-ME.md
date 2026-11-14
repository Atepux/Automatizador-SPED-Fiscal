# Automatizador SPED Fiscal V1 — 1.0.0

Uso mensal em Windows, com a empresa e a competência abertas manualmente no
PVA EFD ICMS/IPI. A V1 não seleciona outra escrituração e não importa, altera,
exclui, valida ou transmite escriturações.

## Como usar

1. Abra o PVA e escolha manualmente a escrituração da empresa e competência.
2. Deixe a janela principal aberta, sem diálogos de salvamento ou avisos.
3. Dê dois cliques em **Iniciar.bat** nesta pasta.
4. Escolha a pasta onde os PDFs devem ser gravados. Cancelar encerra sem geração.
5. Durante a geração, mantenha o computador desbloqueado e o PVA visível;
   evite usar mouse/teclado, cobrir a janela ou trocar de escrituração.
6. Ao terminar, consulte a tabela na janela e o resumo CSV/JSON indicado.

Os nomes são exatamente os do cadastro, sem competência ou CNPJ acrescentados.
Escolha manualmente uma pasta separada por empresa/competência quando desejado.
Os PDFs vão diretamente para a pasta escolhida, sem criar uma subpasta oculta.
Se qualquer nome do lote já existir no destino, a V1 bloqueia antes de iniciar:
escolha outra pasta. Não há sobrescrita, renomeação ou retry automático.

## Destino previamente configurado

Em config/programa.json, preencha destino_padrao com uma pasta, por exemplo:

```json
"destino_padrao": "C:/Relatorios/Empresa/2026-10"
```

Com destino_padrao vazio, a V1 solicita a pasta. Também é possível iniciar
diretamente com o Python configurado:

```powershell
& 'C:\Users\contabil02\AppData\Local\Programs\Python\Python314-32\python.exe' .\principal.py
```

Para indicar um destino específico, acrescente:

```text
--destino "C:\Relatorios\Empresa\2026-10"
```

Esse argumento prevalece sobre destino_padrao. Pastas relativas são resolvidas
a partir da pasta V1. Caminhos Windows em JSON devem usar / ou barras duplas \\.

## Ordem e regras

1. Documentos de entradas.
2. Documentos de saídas.
3. Operações Próprias — garantir Exibir subrelatórios marcada.
4. Operações ST — garantir Exibir subrelatórios marcada.
5. CIAP.
6. Registro de Controle de Créditos Fiscais — opcional; ausência na árvore é ignorada.
7. Operações com Instrumentos de Pagamentos Eletrônicos.
8. Recibo — aguardar até 5 segundos pela abertura/prontidão.

Os demais relatórios não alteram a checkbox. Não há exigência adicional de
estabilidade depois da marcação. A árvore expande somente os pais recolhidos.
Cada relatório tem espera mínima de 2 segundos após clicar. Os cliques usam
limites Java atuais, nunca coordenadas fixas.

Qualquer erro real, mudança do processo/janela principal ou diálogo inesperado
interrompe o lote. Janelas próprias do Recibo são identificadas e observadas
durante seu prazo; janela persistente não mapeada fica pendente, sem fechamento
ou confirmação automática. DIFAL está excluído.

## Configurações e arquivos

- principal.py: entrada da V1; escolhe destino, valida configuração e coordena o lote.
- Iniciar.bat: usa o Python indicado em config/programa.json.
- config/relatorios.json: ordem, nomes exatos e caminhos Java dos oito relatórios.
- config/diagnostico.toml: título do PVA, DLL da bridge e espera mínima de 2 s.
- scripts/: cópias independentes das nove rotinas aprovadas, sem modificações.
- rotinas_aprovadas.json: hashes SHA-256 e referência ao último lote aprovado.
- logs/execucao_.../resumo.csv e resumo.json: status, bytes, páginas e tempos.
- Subpastas dos logs: resultados técnicos de cada etapa, sem conteúdo fiscal.

Nenhuma pasta ou script do projeto original é necessário para iniciar a V1.
As bibliotecas Python instaladas e o PVA/Java do Windows continuam necessários.

## Python e dependências

Configurado para o Python 3.14 de 32 bits já instalado, pyjab, pywin32 e PyMuPDF.
Python precisa ser 3.11 ou posterior. A DLL configurada deve ter arquitetura
compatível com o Python; a combinação comprovada permanece a mesma do teste.
Nada é instalado automaticamente. Para trocar a instalação Python, edite
python_executavel em config/programa.json e faça a revisão offline primeiro.

## Revisão sem acessar o PVA

```text
Iniciar.bat --verificar
```

Ou execute principal.py --verificar pelo Python. O modo confere cadastro,
dependências, caminho/arquitetura da DLL e integridade das rotinas. Não enumera
janelas, não inicia workers de automação e não gera PDFs. Resultado:
logs/revisao_offline.json.

Testes offline:

```text
python -m unittest discover -s tests -v
```

As simulações não substituem o teste real da embalagem V1. A rotina-base gerou
oito PDFs em 68,7753 s, mas a V1 consolidada ainda não foi executada no PVA,
conforme a restrição desta entrega.

## Falhas e execução pendente

O programa não repete automaticamente cliques ou salvamentos. O resumo marca
os itens não alcançados como não executados. Ausência do opcional não é erro;
erro de bridge, ambiguidade ou falha de arquivo continuam interrompendo.

logs/execucao_ativa.lock impede duas execuções concorrentes. A trava é removida
após uma execução encerrada com segurança. Se algum worker permanecer ativo
ou houver interrupção de estado incerto, ela é preservada. Não apague a trava
nem rode novamente sem conferir o resumo e os PIDs registrados. A V1 não fecha
o PVA e não mata o worker abridor por conta própria; uma revisão pode ser
necessária. O worker de gravação tem timeout externo e pode ser encerrado
sem repetir sua ação. Não confirmar janelas desconhecidas automaticamente.

## Limites

A verificação PyMuPDF confirma abertura e estrutura das páginas, não correção
fiscal dos valores. Marcadores textuais são informativos; o marcador do Recibo
ainda é inconclusivo no lote de referência. Não altere os arquivos scripts/
sem revisão, pois a integridade é conferida antes de iniciar.

Esta V1 não tem .exe, agendamento ou troca automática de empresas/competências.
