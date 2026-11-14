# Subrelatórios obrigatórios e exclusão de DIFAL — 13/11/2026

## Cadastro atualizado

Operações Próprias e Operações ST exigem exibir_subrelatorios=true em
config/poc_tres_relatorios.json. Documentos de entradas tem false: a rotina
não marca nem desmarca a opção automaticamente para esse relatório.
Nomes exatos dos PDFs e caminhos hierárquicos foram preservados.

DIFAL RJ e SP estão fora do escopo de geração. A busca no projeto confirmou
que não havia entradas de DIFAL no cadastro executável, que continha apenas
os três relatórios anteriores. Nenhuma entrada DIFAL permaneceu no cadastro.
config/regras_relatorios.json registra a exclusão; a sequência de teste aceita
somente os três IDs autorizados e verifica a regra obrigatória de subrelatórios.
Não foram alterados cadastros fiscais no PVA. O rótulo Diferencial de Alíquota
no inventário histórico docs/arvore_observada.md é uma observação da interface,
não uma entrada de geração; foi preservado como evidência histórica.

## Inspeção de Operações Próprias

O relatório foi aberto pelo caminho completo e clique físico dinâmico aprovado,
sem trocar empresa/competência. A inspeção encontrou um único controle:

- Nome acessível: Exibir subrelatórios... (três pontos).
- Papel: check box.
- Estados: enabled, focusable, visible, showing, opaque, checked.
- is_checked(): true.
- Ação acessível oferecida: clicar.
- Caminho por índices da sessão: [0,1,0,0,0,0,1,0,0,0,1,4]. Não é seletor fixo.

A opção já estava marcada. Não houve clique, alternância ou mudança no checkbox.
Nenhum PDF foi salvo. Não foi necessário provocar mudança para confirmar o
estado; isso preserva a regra de não alternar indiscriminadamente.

## Controle preparado

scripts/subrelatorios.py fornece garantir_subrelatorios:

1. Encontra univocamente o checkbox pelo nome e papel; exige visível/habilitado.
2. Lê checked antes da ação.
3. Se true, não clica. Se false, executa uma única ação acessível do checkbox,
   usando a ação que ele expõe (clicar), sem coordenadas fixas ou retry.
4. Confirma checked por leitura posterior; espera quatro observações estáveis
   de checked e ausência de busy. Interrompe se houver modal, ambiguidade ou
   prazo excedido. Não considera apenas o retorno da ação como prova.
5. A integração redescobre Salvar e exige habilitação depois da opção.

A rotina foi integrada como etapa anterior ao salvamento para os dois IDs
obrigatórios no fluxo parametrizado. Para os demais casos não é chamada.
O teste de três relatórios continua com trava de autorização anterior; não
foi reexecutado. Os PDFs anteriores não foram refeitos ou modificados.

## Recarregamento e limites

Não foi possível medir o recarregamento causado por alteração porque o checkbox
já estava checked e não foi alterado nesta prova. Logo, não afirmar que marcar
dispensa espera ou que os subrelatórios já foram verificados no conteúdo do PDF.

A implementação preparada verifica estabilidade de estado e disponibilidade
de Salvar; esses sinais não provam, sozinhos, término de toda reconstrução
interna do relatório. A transição desmarcado→marcado e seu impacto no conteúdo
ainda requerem teste dedicado. A ação de marcar foi preparada com base na API
exposta, mas não executada nesta etapa. Nenhum salvamento com essa nova regra
foi testado. Registrar essa limitação até a próxima autorização.

Evidência: logs/subrelatorios_20261113_115924/resultado.json e
inspecao.resultado.json. Diagnóstico em scripts/diagnosticar_subrelatorios.py.
Configuração sem dados fiscais. Nenhuma instalação ou execução em lote realizada.
