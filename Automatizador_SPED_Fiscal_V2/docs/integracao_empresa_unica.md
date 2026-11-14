# Integração de uma empresa — preparada e validada offline

Entrada: `executar_empresa.py`. Sem `--executar` ou com `--verificar`, realiza
apenas revisão offline, sem consultar o PVA. O diagnóstico antigo permanece
disponível em `principal.py`. Nenhum relatório foi executado nesta etapa.

## Fluxo integrado

1. Validar o cadastro aprovado e conferir arquivos existentes no destino antes
   de qualquer acesso à interface.
2. Consultar os comandos Java Abrir/Fechar, sem clicar, para distinguir PVA
   vazio de escrituração aberta. Diálogos e estados ambíguos bloqueiam o fluxo.
3. Se aberta, exigir leitura do rodapé e identidade correspondente. Reutilizar
   sem fechar nem abrir novamente. Outra identidade ou rodapé ilegível interrompe.
4. Se vazio, abrir somente a lista de escriturações pelo comando aprovado;
   manter o processo abridor vivo durante a seleção Java. Exigir correspondência
   única, seleção confirmada, um único Ok e identidade confirmada no rodapé.
5. Confirmar novamente a identidade antes da geração e manter o mesmo PID/HWND.
6. Entregar a geração às cópias intactas da rotina V1, na ordem cadastrada.
   Nenhum comando de fechamento é disponibilizado pelo adaptador da integração.

As oito entradas mantêm nomes exatos, expansão dinâmica, clique físico dinâmico,
espera mínima de 2 segundos após abertura de relatório e validação PyMuPDF.
Próprias/ST exigem subrelatórios marcados; demais não alteram essa opção.
Recibo mantém espera especial de até 5 segundos; Controle de Créditos Fiscais
é opcional; DIFAL permanece excluído. Nenhuma repetição automática após falhas.

## Destino e registros

Destino: `<destino-base>/<alias da empresa>/<AAAA-MM>/`, preservando os nomes
originais dos PDFs. O alias deve ser fornecido explicitamente, sem CNPJ.
Arquivo existente bloqueia o lote; não é renomeado nem sobrescrito.

O registro da execução fica em `logs/empresa_unica_<identificador>/`, com
`resumo.json` e `resumo.csv` da V2, inclusive em interrupções, e os registros
aprovados da geração em `relatorios/`. Não se persistem critérios de identidade
nem o texto do rodapé. Critérios entram pela entrada padrão do auxiliar.

Os registros internos originais da geração preservam o caminho de destino,
como na V1; a pasta escolhida não deve conter CNPJ ou outro dado fiscal sensível.

Uma trava impede execuções simultâneas dessa entrada. Interrupções preservam a
trava para revisão, sem nova tentativa, sem fechar escrituração e sem encerrar
o PVA. Eventual processo abridor bloqueado é preservado e registrado.

## Revisão offline concluída

- 25 testes aprovados: 13 existentes e 12 novos cenários de integração.
- Reutilização da identidade correta sem abertura; abertura somente se vazia.
- Bloqueio por outra identidade, rodapé ilegível, modal, timeout, ambiguidade,
  abertura não confirmada ou processo auxiliar pendente.
- Divergência imediatamente antes da geração impede os relatórios.
- Arquivo existente impede até o acesso ao PVA e permanece intacto.
- Opcional ausente permite continuar; erro real interrompe sem repetição.
- Oito relatórios e regras de checkbox/Recibo/destino conferidos.
- JSON/CSV conferidos e ausência de CNPJ nos registros simulados verificada.
- Hashes dos dez componentes copiados aprovados conferidos; importações V2.

Os relatórios dos testes são respostas simuladas, sem acesso ao PVA e sem PDFs.
A integração real de abertura mais geração ainda aguarda autorização de teste
para uma única empresa.

## Preparação do teste futuro

Revisão segura: `python executar_empresa.py --verificar`.

Somente após autorização: `python executar_empresa.py --executar --empresa
EMPRESA_TESTE --destino-base PASTA_ESCOLHIDA`. A entrada solicita os critérios;
o CNPJ é ocultado no terminal e não é salvo em arquivo de configuração.
Também aceita `--criterios-stdin` para critérios JSON via entrada padrão.

Os comandos acima documentam a entrada preparada, sem terem sido usados para
executar a geração no PVA nesta etapa. Nenhuma automação de múltiplas empresas.
