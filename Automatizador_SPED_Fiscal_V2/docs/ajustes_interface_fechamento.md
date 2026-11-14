# Ajustes após o primeiro uso multiempresas

O registro `multi_20261113_164935_5c56c0` comprova a geração dos oito PDFs da
primeira empresa. A consulta `001_antes_fechar` terminou em RuntimeError;
nenhuma pasta `001_fechar` foi criada. Portanto, Fechar não chegou a ser acionado.
O log antigo não continha pilha/motivo e não permite provar a causa exata.

Fragilidade corrigida: a busca do menu antes continuava percorrendo toda a
interface depois de encontrar a barra principal, incluindo o visualizador já
carregado e seus controles profundos. Agora retorna assim que identifica a
barra correta, não percorre áreas de visualização e é compartilhada entre a
consulta de estado e os comandos Abrir/Fechar. Os erros novos registram pilha
e motivos técnicos controlados, sem texto fiscal. A identidade do rodapé
continua obrigatória; nenhum estado desconhecido libera fechamento ou próxima empresa.

A interface recebeu novo cabeçalho, cores, tipografia e espaçamento. As caixas
são imagens independentes do texto; só o acerto no elemento da imagem alterna
a seleção. Categorias e texto não a alternam. A competência insere / após MM,
aceita colagem de MMAAAA e permite apagar com Backspace/Delete.

Tipo, Suporte e opção Opcional foram removidos da tela. Todos os relatórios
selecionados são obrigatórios, inclusive Controle de Créditos Fiscais. A migração
na próxima abertura do cadastro zera as opções antigas, conservando seleções,
nomes personalizados e empresas. Regras internas de segurança para interações
não suportadas continuam vigentes.

Travas de execuções antigas só são arquivadas se os PIDs tiverem terminado e
nenhum auxiliar V2 permanecer. Não se mata processo nem se repete interação.
Reinicie a interface para carregar os novos arquivos e aplicar a migração.

61 testes offline aprovados: incluem clique apenas na imagem, preenchimento
da barra, migração, relatórios obrigatórios, interrupção por indisponibilidade,
busca do menu sem visitar o visualizador e proteção de travas com auxiliares.
A V1 permanece intacta. Nenhum novo lote, fechamento ou troca real foi executado
nesta etapa. O fechamento ainda precisa de reteste autorizado no PVA.
