# Espera de carregamento — correção V2

O usuário confirmou que o diálogo observado após Ok era o carregamento da
escrituração. A abertura não é instantânea. O teste partindo do PVA vazio
encontrou uma correspondência única, selecionou-a e acionou Ok uma única vez.
Uma leitura posterior do rodapé confirmou a identidade, sem repetir abertura.

A V2 agora aguarda até 30 segundos pela conclusão da abertura. Considera que
o diálogo de carregamento pode surgir depois do desaparecimento da seleção.
Não interage com essas janelas. Apenas prossegue sem diálogos, com a principal
habilitada e com CNPJ/período correspondentes no rodapé. Divergência de um
rodapé legível interrompe. Diálogo persistente ou rodapé ausente expiram o prazo.

Na geração, a espera mínima de 2 segundos após o clique no relatório permanece.
Janelas adicionais são aguardadas sem interação dentro do limite existente de
12 segundos; não se consulta nem aciona Salvar enquanto persistirem. O Recibo
mantém limite especial de 5 segundos. Não há novo clique no relatório em caso
de demora; janela persistente ou controles indisponíveis interrompem o lote.

Essa mudança está exclusivamente na cópia V2 de ativar_operacoes_proprias.py,
com hashes original/atual e motivo em config/ajustes_v2.json. O manifesto de
preservação original não foi reescrito. As demais rotinas copiadas continuam
conferidas pelos hashes originais. A pasta V1 não foi modificada.

Último teste real antes da correção da espera: Entradas gerado e validado
(3 páginas); Saídas interrompido por janela adicional; demais não executados.
JSON/CSV foram gerados. Nenhum clique ou salvamento foi repetido após essa falha.

25 testes offline passaram após a correção. A nova espera ainda não foi
validada numa nova execução de relatórios no PVA.
