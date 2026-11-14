# Salvamento único — 13/11/2026

Prova de conceito concluída com autorização explícita do usuário.

- Destino: saida/TESTE_FICTICIO/relatorio_teste.pdf, sob a pasta do projeto.
- A pasta foi criada previamente e a ausência do arquivo foi conferida antes
  do preenchimento e imediatamente antes da ação de salvamento.
- Janela Salvar SunAwtDialog, HWND 658798, pertencente ao mesmo processo da
  janela principal do PVA, PID 14432. O executável foi conferido previamente:
  C:\Programas\Programas SPED\Fiscal\jre\bin\javaw.exe.
- Campo Nome do arquivo identificado por nome e papel acessível; caminho
  absoluto preenchido por pyjab e confirmado integralmente por leitura.
- Botão Salvar acionado por ação acessível Java uma única vez, sem coordenadas
  ou teclas. Nenhuma repetição automática.
- A janela Salvar fechou e não foi detectada nova janela durante a espera.
- Arquivo criado: 28.688 bytes, 3 páginas.
- PyMuPDF abriu o arquivo como PDF, sem senha e sem reparo; todas as páginas
  foram carregadas sem extrair texto ou conteúdo fiscal.
- Não houve dificuldade com o caminho absoluto, incluindo espaços.
- Configuração de acessibilidade preservada.

Esta conferência cobre abertura e estrutura do PDF; não verifica conteúdo
fiscal, aparência das páginas ou correção da escrituração.
Nenhuma empresa ou relatório foi trocado. Nenhum outro salvamento foi feito.
Nenhum PDF foi enviado para serviços externos.

Script: scripts/salvar_pdf_unico.py. Evidência técnica:
logs/salvamento_unico_20261113_103205.json.

Uma trava persistente em logs/salvar_unico_acionado.lock impede repetir a ação
em nova execução do script. O PDF existente também bloqueia novas tentativas.
A trava é específica desta prova de conceito, não uma solução de execução em lote.
