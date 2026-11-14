Versão 2.3 distribuível: veja GUIA_DISTRIBUICAO.md e entrega/Automatizador_SPED_Fiscal_V2.exe. Interface lateral azul, edição direta de nomes na tabela e preparo guiado do Java. A execução de duas empresas foi confirmada pelo usuário antes do empacotamento.

# Automatizador SPED Fiscal V2 — etapa 1, diagnóstico

**Interface gráfica e coordenação multiempresas disponíveis:** abra `Iniciar.bat`.
Leia `INSTRUCOES_INTERFACE.md`. Cadastro SQLite, importação CSV/XLS/XLSM e
configurações individuais implementados; 55 testes offline aprovados.
Fechamento e troca real entre empresas aguardam autorização de teste.
Os registros abaixo preservam as etapas anteriores do projeto.

Integração de **uma empresa** preparada em `executar_empresa.py`, com revisão
offline aprovada e 25 testes passando. A execução real aguarda autorização.
Consulte `docs/integracao_empresa_unica.md`. A V1 permanece preservada.

Atualização: identidade da escrituração já aberta confirmada pelo rodapé Java,
com CNPJ e período correspondentes aos critérios autorizados. Abertura aprovada.
Veja docs/confirmacao_rodape.md e o histórico em docs/teste_selecao_unica.md.
O diagnóstico inicial permanece
sem ações e a rotina de seleção exige entrada explícita dos critérios.
Veja também docs/janela_abrir_escrituracao.md e config/controles_selecao.json.
Os tópicos abaixo preservam a preparação inicial; a pendência de identificar
os cabeçalhos foi resolvida, mas a confirmação da identidade após abrir continua pendente.

A V1 foi confirmada funcional pelo usuário e permanece intacta. Esta V2 é uma
pasta independente; reutiliza cópias dos componentes da V1 para evolução futura.
Não requer executar ou importar arquivos da pasta V1. As bibliotecas instaladas
e o PVA/Java continuam sendo dependências do ambiente.

## Disponível nesta etapa

- principal.py / Iniciar_Diagnostico.bat: inspeção Java somente de leitura,
  com timeout externo de 25 segundos. Não abre menus, clica, seleciona, muda
  foco ou digita. Não executa relatórios e não salva PDFs.
- scripts/diagnostico_escrituracoes.py: lista controles/papéis/estados e ações
  acessíveis disponíveis, sem executá-las.
- logs/diagnostico_.../: resumo e interface sanitizada. Somente rótulos fixos
  permitidos são preservados; nomes dinâmicos, valores e conteúdo fiscal omitidos.
- geracao_v1.py e nove scripts aprovados: cópias para reutilização posterior,
  sem modificações. Não executar geracao_v1.py nesta etapa: ele é o componente
  de geração original, que aguarda futura coordenação/autorizações da V2.
- config/relatorios.json e diagnostico.toml: cópias independentes da V1.
- v1_preservacao.json: impressão digital agregada da origem e hashes das cópias.

## Resultado e pendências

Consulte docs/diagnostico_selecao.md. O menu Escrituração Fiscal → Abrir foi
identificado, mas está desabilitado no estado observado. A lista de escriturações
não foi aberta: seleção, colunas, filtros e confirmação de CNPJ/período ainda
precisam ser inspecionados após nova autorização ou abertura manual pelo usuário.

A V2 não está habilitada para troca de empresa/competência ou geração coordenada.
Não executar o diagnóstico repetidamente para contornar falhas. Nenhum pacote
foi instalado e nenhuma configuração Java foi alterada nesta preparação.
