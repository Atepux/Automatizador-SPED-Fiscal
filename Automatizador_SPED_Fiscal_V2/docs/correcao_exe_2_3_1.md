# Correção do executável 2.3.1

Os registros enviados pelo usuário mostraram duas causas concretas:

- Em algumas tentativas, o auxiliar Abrir não confirmou o foco e interrompeu
  antes de qualquer clique no menu. O processo principal agora autoriza o auxiliar
  a ativar a janela. A ativação aguarda a resposta do Windows e usa a vinculação
  temporária das threads como alternativa, sem teclas e sem cliques de tentativa.
- Quando Abrir funcionava, a seleção falhava com FileNotFoundError ao carregar
  config/diagnostico.toml. Módulos importados pelo PyInstaller tinham __file__
  em uma pasta diferente dos scripts executados por runpy. Derivar a raiz com
  parents[1] fazia procurar a configuração fora de _internal. Todos os módulos
  operacionais agora usam a raiz explícita RESOURCES do runtime.

Foi acrescentada conferência dos recursos antes de iniciar o processamento.
Erros técnicos durante a abertura interrompem o lote, sem avançar a outra
empresa nem apresentar a falha como simples ausência/ambiguidade de cadastro.

O autoteste anterior verificava interface, PDF sintético e IPC, mas não conferia
as raízes dos módulos de seleção e geração. Agora o próprio EXE importado
confere os nove módulos operacionais e simula duas empresas, 16 PDFs e dois
fechamentos. Esse teste continua sem interagir com o PVA.

Validação: 72 testes offline aprovados; autoteste do runtime e do iniciador
2.3.1 aprovados em perfil isolado. A V1 permanece preservada e não foram
modificados cadastros, travas ou resultados existentes do usuário.

Fechar o programa antigo antes de abrir a versão 2.3.1 permite que a recuperação
segura de travas identifique o PID anterior encerrado. Nenhum auxiliar ativo é
encerrado automaticamente. O PVA precisa estar sem escrituração e sem diálogos
para iniciar um novo lote.

Nenhum lote real foi executado nesta correção. A ativação e o fluxo fiscal no
executável atualizado ainda precisam de confirmação no teste real do usuário.
