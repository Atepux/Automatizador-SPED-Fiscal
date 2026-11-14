# Validação de subrelatórios — 13/11/2026, 12:18

Resultado geral: NÃO APROVADO. Foi criado somente o PDF de Operações Próprias.
Operações ST não foi iniciado. Não houve nova execução após a interrupção.

## Navegação e checkbox de Operações Próprias

- Escrituração Fiscal e Apuração do ICMS já expandidos: nenhuma ação.
- Relatórios de Registros Fiscais recolhido: uma ação toggleexpand, seguida
  de confirmação expanded por novas referências Java.
- Folha aberta por um clique físico dinâmico. Salvar passou de ausente a disponível.
- Checkbox inicialmente false, lido às 15:18:08.076 UTC.
- Uma ação de marcação, de 15:18:08.078 a 15:18:08.479 UTC. Não foi desmarcado.
- A espera de estabilidade excedeu o prazo de dez segundos. Não houve registro
  suficiente das amostras para atribuir a causa exata ou provar o término do
  recarregamento nessa etapa.
- Em um novo processo antes da exportação, a opção foi encontrada true,
  permaneceu true em leituras estáveis e Salvar estava habilitado. Nenhum novo
  clique no checkbox. Busy não foi observado nessa confirmação.

## Falha de controle identificada

Apesar do TimeoutError da etapa de estabilidade, o worker manteve sucesso=true
da abertura anterior do relatório. O supervisor verificou esse sucesso residual
e permitiu avançar para a exportação. Isso violou a regra de interromper diante
de falha. A confirmação posterior do checkbox não apaga essa falha de controle.
O teste NÃO deve ser considerado aprovado, mesmo com PDF válido.

Após gravar o primeiro PDF, o agregador também encontrou AttributeError ao
tratar um resultado de subrelatórios ausente como dicionário. Isso interrompeu
a sequência antes de ST. Os registros brutos foram preservados para auditoria;
os flags de sucesso isolados do primeiro fluxo não representam conformidade
da integração. O resumo geral já registra sucesso=false.

## PDF gerado e comparação

Nome preservado: Registros Fiscais da Apuração do ICMS_Operações Próprias.pdf.
Pasta: saida/TESTE_SUBRELATORIOS_20261113_121806.

| Relatório | Anterior | Atual | Tempo | Situação |
| --- | --- | --- | --- | --- |
| Operações Próprias | 3.539 bytes, 1 página | 18.624 bytes, 3 páginas | 18,0201 s | PDF íntegro; integração reprovada por falha anterior |
| Operações ST | 3.527 bytes, 1 página | Não gerado | Não iniciado | Pendente |

PyMuPDF abriu o PDF novo sem senha/reparo e carregou as três páginas. Marcadores
Operações Próprias e Apuração do ICMS encontrados, com texto processado apenas
em memória. Uma única confirmação de salvamento, sem sobrescrita; diálogo fechado
ao final, todos os workers encerraram normalmente.

O texto normalizado difere do anterior. Porém, a busca por novos marcadores
genéricos de subrelatório/detalhamento/ajustes/obrigações não encontrou evidência
adicional identificável. O aumento de bytes/páginas NÃO comprova, isoladamente,
inclusão correta de subrelatórios. A comparação foi feita offline após a
interrupção, sem nova ação no PVA ou conteúdo fiscal nos logs.

## Correções efetuadas sem reexecutar o PVA

- Qualquer exceção do worker agora define sucesso=false.
- O supervisor rejeita erro_tipo mesmo se um sucesso residual estiver presente.
- Exportação obrigatória exige resultado completo de subrelatórios: final=true,
  estabilidade_confirmada=true e salvar_habilitado=true. Ausência ou null bloqueiam.
- Agregador trata resultado ausente sem AttributeError.
- A espera de subrelatórios agora renova contexto, checkbox e Salvar a cada
  amostra, pois marcar pode reconstruir o visualizador. A versão anterior
  consultava o Salvar encontrado antes da marcação, um possível fator para o
  timeout. A causa exata histórica não foi comprovada.
- As novas amostras registram somente checked/busy/habilitação, sem texto fiscal.

Verificação offline usando o registro real com TimeoutError/sucesso residual
confirmou bloqueio antes da exportação. Casos sem resultado, null e estabilidade
false também foram bloqueados; resultado completo foi aceito. Compilação
sintática aprovada. Nenhum novo clique/salvamento foi executado para testar
essas correções, e a nova espera ainda exige validação autorizada.

Não foram executados DIFAL, outros relatórios ou troca de empresa/competência.
Nenhuma escrituração alterada/validada/transmitida. Regra permanece com
salvamento_com_subrelatorios_validado=false.

Evidências: logs/validar_subrelatorios_20261113_121806/resultado.json,
comparacao_operacoes_proprias.json e subpasta 01_operacoes_proprias. Tempos e
estados do checkbox estão em relatorio/resultado.subrelatorios.jsonl e
abrir_salvar/A.eventos.jsonl. Não remover travas para repetição automática.
