# Prova de conceito — 13/11/2026

Conexao pyjab confirmada, sem cliques, teclas, ativacao de janela ou operacoes
sobre escrituracoes. O mesmo processo permaneceu aberto e respondendo ao final.

## Ambiente efetivamente utilizado

- Python 3.14.10 de 32 bits; pyjab 1.12.0 e pywin32 ja instalados.
- Processo javaw.exe, PID 14432, HWND 1510638, classe SunAwtFrame.
- Executavel: C:\Programas\Programas SPED\Fiscal\jre\bin\javaw.exe.
- Runtime privado Eclipse Adoptium Temurin 21.0.6+7-LTS, 64 bits.
- Cliente bridge: C:\Program Files (x86)\Java\jre1.8.0_511\bin\WindowsAccessBridge-32.dll.
- get_version_info retornou VMVersion e versoes bridge 21.0.6.
- A diferenca entre a arquitetura do Python e a do PVA nao impediu a leitura.
- Um Python 3.12.10 de 64 bits foi localizado em
  C:\Coleta NFSe Nacional\App\Python312\python.exe, sem pyjab/pywin32.
  Nao e um inventario exaustivo de todas as instalacoes Python.

## Controles observados

85 elementos: 16 botoes, 11 menus, 35 itens de menu, uma barra de menus,
uma barra de ferramentas, uma lista de abas e outros conteineres/separadores.
Os 11 menus incluem submenus; nao sao 11 menus principais.

Rotulos preservados pela lista permitida: Abrir, Ajuda, Configuracoes,
Editar, Excluir, Fechar, Gerar, Importar, Relatorios, Sair e Transmitir
(o JSON mantem a acentuacao original). Esses elementos foram apenas lidos.
Menus fechados tambem expuseram filhos; nenhum menu precisou ser aberto.

Foram registrados papel acessivel, estados em ingles, indice no pai, caminho
de indices e quantidade de filhos. Estados incluem enabled, focusable,
visible, showing e selectable; nem todos aparecem em todos os elementos.
O HWND identifica a janela nesta sessao. Caminhos/indices nao sao IDs estaveis.

## Limites e dificuldades

- O isolamento inicial ocultava o PVA e impedia CIM; o diagnostico foi
  executado fora desse isolamento com acesso somente de leitura ao PVA.
- Os 16 botoes da barra nao apresentaram nome acessivel. Descricoes e tooltips
  nao foram coletados nesta etapa, para reduzir exposicao de dados.
- Nomes fora da lista permitida foram omitidos mesmo quando possivelmente
  estaticos. Nao representam falha de acesso.
- A leitura foi limitada a profundidade 8 e 250 elementos; nao constitui
  inventario completo de todas as telas. Tabelas, listas, arvores e campos
  de texto nao tem seus descendentes percorridos.
- O pyjab pode regravar a configuracao de acessibilidade automaticamente;
  essa operacao foi bloqueada em memoria. O arquivo permaneceu identico.
- O gerenciador de contexto do pyjab pode encerrar o processo ao sair;
  nao foi usado. A conexao foi liberada por detach().

## Verificacoes

Execucao real sem erro de conexao/inspecao, compilacao sintatica aprovada,
JSON sem sequencias numericas de CNPJ de 14 digitos e nomes dinamicos omitidos.
Nenhuma biblioteca instalada ou configuracao do Windows/Java alterada.

Proxima etapa proposta: mapear os seletores do caminho de um relatorio,
priorizando menus com rotulos semanticos. Navegacao, selecao de empresa e
geracao de PDF continuam pendentes de autorizacao especifica.
