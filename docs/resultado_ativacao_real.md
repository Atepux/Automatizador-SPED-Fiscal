# Ativação real de Operações Próprias — 13/11/2026

Teste aprovado nesta sessão: um clique físico no controle Java abriu o relatório
no visualizador e disponibilizou Salvar. Nenhum PDF foi salvo.

## Correção do diagnóstico

AccessibleSelection pode apenas destacar a folha, sem disparar o comportamento
de abertura do PVA. O usuário observou essa diferença e o teste atual comprovou
uma forma de ativação. O estado selected sozinho não comprova abertura. Esta
regra substitui a suposição anterior de atualização automática ao selecionar.

## Inspeção e escolha do método

O caminho foi resolvido por nomes exatos entre filhos imediatos:
Escrituração Fiscal → Relatórios de Registros Fiscais → Apuração do ICMS →
Operações Próprias. Pais expandidos e nós visible/showing confirmados.

- Folha: nenhuma ação acessível disponível.
- Pai Apuração do ICMS: apenas toggleexpand.
- Árvore: nenhuma ação acessível disponível.
- Folha não expõe estado focusable; a árvore expõe focusable.

Não há ação acessível de ativação identificada. Teclado foi considerado, mas
não executado: o foco da árvore não comprova um binding Enter/Space que abra
a folha, e a semântica desse comando não foi identificada nesta inspeção.
Isso não prova que ativação por teclado seja impossível.

## Clique dinâmico e resultado

A primeira inspeção retornou limites compatíveis com janela minimizada.
A janela foi restaurada e colocada em primeiro plano sem enviar teclas. Os
limites do nó foram lidos novamente, convertidos para coordenadas físicas e
o ponto foi conferido como pertencente à janela do PVA.

Foi executado uma única vez JABElement.click(simulate=True). Essa chamada usa
o centro dos limites atuais do nó, com conversão de coordenadas do pyjab.
Não há posição fixa na configuração. Os números no log são evidência da
execução, não seletores reutilizáveis.

Antes do clique, não havia botão Salvar utilizável no visualizador. Depois:

- Operações Próprias passou a selected.
- Um botão visível e habilitado com descrição acessível Salvar foi localizado.
- Não surgiu nova janela e não houve repetição de clique.
- Configuração de acessibilidade permaneceu idêntica.

Essa transição atende ao critério desta etapa: ativação do relatório e Salvar
disponível no visualizador. O botão Salvar não foi acionado e não houve gravação.
Não foram coletados textos fiscais, imagens ou dados de empresa/competência.

## Recomendação e limites

Resolver o caminho por nome, confirmar pais expandidos, restaurar a janela,
confirmar primeiro plano, obter limites Java atuais, verificar o ponto e dar
um clique físico. Confirmar o resultado pelo visualizador/Salvar, não somente
selected. Interromper se houver ambiguidade, diálogo inesperado ou falha.

Requer sessão Windows interativa, janela desobstruída e limites válidos. A
conversão DPI usa o pyjab instalado e só foi comprovada na configuração atual;
outros monitores/escalas exigem teste próprio. Um botão Salvar já disponível
antes de uma futura ativação não constitui, sozinho, evidência de atualização.
Não implementar lote a partir deste único teste.

A função focus() desta versão de pyjab pode enviar espaço à janela que tinha
foco. O script usa restauração/primeiro plano sem essa função e confirma o foco
antes do clique, evitando o envio dessa tecla fora do alvo.

Script: scripts/ativar_operacoes_proprias.py, modos inspect e click. Supervisor
com timeout externo de 30 segundos e trava persistente que impede novo clique.
Evidências: logs/ativacao_operacoes_inspect_20261113_110427.json e
logs/ativacao_operacoes_click_20261113_110501.json.
