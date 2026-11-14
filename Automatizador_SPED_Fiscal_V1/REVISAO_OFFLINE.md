# Revisão offline da V1 — 13/11/2026

Resultado aprovado sem acesso ao PVA, sem cliques e sem novos relatórios/PDFs.

- principal.py --verificar: aprovado; oito relatórios, sete principais e um opcional.
- Python detectado: 3.14, 32 bits; DLL configurada existente e compatível.
- Bibliotecas pyjab, pywin32 e PyMuPDF disponíveis; nenhuma instalação.
- Nove módulos importados exclusivamente de scripts/ da V1; hashes idênticos
  às cópias das rotinas aprovadas do lote lote_completo_20261113_151456.
- Iniciar.bat --verificar: iniciou o Python configurado e retornou exit code 0.
- Nove testes offline aprovados em 0,207 s: ordem/nomes, conflitos antes de
  automação, sequência dos oito, opcional ausente, interrupção sem retry,
  mudança de janela/processo, worker pendente, configuração inválida e
  independência/integridade dos módulos.
- Resumos JSON/CSV exercitados em diretórios temporários com runner e
  identificação do PVA simulados. Nenhum subprocesso de automação real.

Resultado automático: logs/revisao_offline.json. Testes:
tests/test_v1_offline.py. Os arquivos do projeto original e seus resultados
foram preservados; a V1 trabalha com configurações e logs próprios.

O iniciador .bat foi testado somente com --verificar. Sua abertura normal
inicia o lote depois de escolher o destino. A execução real da V1 fica pendente
de autorização, e não se confunde com o teste aprovado das rotinas-base.
