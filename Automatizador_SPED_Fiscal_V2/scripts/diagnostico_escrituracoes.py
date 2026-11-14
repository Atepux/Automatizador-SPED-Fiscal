"""Somente leitura Java: nenhum clique, tecla, foco ou selecao."""
from datetime import datetime,timezone
from ctypes import byref
import json
import logging
from pathlib import Path
import re
import unicodedata
import tomllib

from execucao_runtime import RESOURCES
ROOT=RESOURCES
STATIC={
    'escrituracao','escrituracoes','escrituracao fiscal','abrir','abrir escrituracao',
    'abrir escrituracoes','selecionar escrituracao','selecao de escrituracao',
    'fechar','importar','importar escrituracao','excluir','editar','novo','nova',
    'cnpj','cnpj/cpf','cpf/cnpj','cpf','periodo','periodo inicial','periodo final',
    'data inicial','data final','dt. inicial','dt. final','nome','nome empresarial',
    'razao social','empresa','contribuinte','competencia','inscricao estadual',
    'arquivo','perfil','versao','tipo','finalidade','ok','cancelar','confirmar',
    'selecionar','pesquisar','filtro','filtrar','localizar','relatorios',
    'configuracoes','ajuda','ferramentas','validar','transmitir','sair','visualizar',
    'recuperar copia de seguranca','gerar copia de seguranca','dados da escrituracao',
    'data inicio','data fim','inicio','fim','periodo da escrituracao','situacao',
    'cnpj do contribuinte','data de inicio','data de fim','data de termino',
    'nome do contribuinte','inscricao','buscar','abrir escrituracao fiscal'
}


def key(text):
    text=text.strip().replace('&','').split('\t')[0].rstrip('.…: ')
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c))


def safe_name(text):
    return text if key(text) in STATIC else '[omitido]' if text else ''


def safe_header(text):
    # Somente contexto de cabecalho da tabela; nunca celulas de dados.
    import html
    label=' '.join(html.unescape(re.sub(r'<[^>]+>',' ',text)).split())
    sensitive=bool(re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{11,}',label))
    return label if label and len(label)<=120 and not sensitive else safe_name(text)


def inspect(output):
    import win32gui as g
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from pyjab.accessibleinfo import AccessibleActions,AccessibleTableInfo,AccessibleTableCellInfo
    logging.disable(logging.CRITICAL)
    result={'versao':'2.0.0-diagnostico','timestamp_utc':datetime.now(timezone.utc).isoformat(),
            'somente_leitura':True,'janelas':[],'controles':[],'limites':{'profundidade':22,'controles':650}}
    props=Path.home()/'.accessibility.properties';before=props.read_bytes() if props.exists() else None
    def block(self):raise RuntimeError('alteracao_acessibilidade_bloqueada')
    Service.__wrapped__.enable_bridge=block
    drivers=[];held=[]
    try:
        visible=[]
        g.EnumWindows(lambda h,_:visible.append(h) if g.IsWindowVisible(h) else None,None)
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        roots=[h for h in visible if g.GetWindowText(h).startswith(cfg['titulo_prefixo'])]
        if len(roots)!=1:raise RuntimeError('pva_ausente_ambiguo')
        main=roots[0];_,pid=win32process.GetWindowThreadProcessId(main)
        result.update(pid_pva=pid,hwnd_principal=main)
        # Preferir uma lista/modal ja aberta manualmente; nunca conectar a
        # principal bloqueada por modal nem criar dois drivers sob a mesma modal.
        dialogs=[h for h in visible if win32process.GetWindowThreadProcessId(h)[1]==pid and g.GetClassName(h) in {'SunAwtDialog','#32770'}]
        targets=dialogs if dialogs else [main]
        if len(targets)!=1:raise RuntimeError('multiplos_dialogos_nao_escolher_automaticamente')
        for hwnd in targets:
            result['janelas'].append({'hwnd':hwnd,'classe':g.GetClassName(hwnd),
                'titulo':safe_name(g.GetWindowText(hwnd)),'modal_windows':hwnd!=main})
            d=JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5);drivers.append(d)
            def walk(el,indices,parent_names,depth=0):
                if depth>22 or len(result['controles'])>=650:
                    result['truncado']=True;return
                role=el.role_en_us
                raw=el.name
                label=safe_name(raw)
                names=parent_names+([label] if label and label!='[omitido]' else [])
                states=el.states_en_us
                row={'janela_hwnd':hwnd,'indices':indices,'papel':role,'nome':label,'caminho_rotulos_estaticos':names,
                     'estados':states,'filhos':el.children_count,'selecao_acessivel':el.accessible_selection,
                     'texto_acessivel':el.accessible_text}
                # Apenas presenca, nunca valores de identificacao fiscal.
                row['indicio_identificador_fiscal_no_nome']=bool(re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|(?<!\d)\d{14}(?!\d)',raw))
                if role in {'menu','menu item','push button'} and el.accessible_action:
                    info=AccessibleActions();d.bridge.getAccessibleActions(d.vmid,el.accessible_context,byref(info))
                    allowed={'click','clicar','toggleexpand','togglepopup'}
                    row['acoes_disponiveis']=[info.actionInfo[i].name if info.actionInfo[i].name in allowed else '[acao_omitida]' for i in range(min(info.actionsCount,16))]
                result['controles'].append(row)
                if role=='table':
                    info=AccessibleTableInfo()
                    if d.bridge.getAccessibleTableInfo(d.vmid,el.accessible_context,byref(info)):
                        row['tabela']={'linhas':info.rowCount,'colunas':info.columnCount,'cabecalhos':[]}
                        header=AccessibleTableInfo()
                        if d.bridge.getAccessibleTableColumnHeader(d.vmid,el.accessible_context,byref(header)):
                            for col in range(min(header.columnCount,30)):
                                cell=AccessibleTableCellInfo()
                                if d.bridge.getAccessibleTableCellInfo(d.vmid,header.accessibleTable,0,col,byref(cell)) and cell.accessibleContext:
                                    c=JABElement(d.bridge,hwnd,d.vmid,cell.accessibleContext);held.append(c)
                                    row['tabela']['cabecalhos'].append({'coluna':col,'nome':safe_header(c.name)})
                            for field in ['caption','summary','accessibleContext','accessibleTable']:
                                ref=getattr(header,field)
                                if ref:d.bridge.releaseJavaObject(d.vmid,ref)
                        for field in ['caption','summary','accessibleContext','accessibleTable']:
                            ref=getattr(info,field)
                            if ref:d.bridge.releaseJavaObject(d.vmid,ref)
                # Nao percorrer registros de empresas, documentos ou conteudo fiscal.
                if role in {'table','list','tree','text','password text'}:return
                for i in range(min(el.children_count,650)):
                    if len(result['controles'])>=650:result['truncado']=True;break
                    ctx=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
                    if ctx:
                        c=JABElement(d.bridge,hwnd,d.vmid,ctx);held.append(c)
                        walk(c,indices+[i],names,depth+1)
            walk(d.root_element,[],[])
        result['conexao_java']=True
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
    finally:
        for el in reversed(held):
            try:el.release_jabelement()
            except Exception:result['aviso_liberacao']=True
        for d in reversed(drivers):
            try:d.detach()
            except Exception:result['aviso_detach']=True
        result['acessibilidade_preservada']=before==(props.read_bytes() if props.exists() else None)
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'log':str(output),'conexao_java':result.get('conexao_java',False),
                          'controles':len(result['controles']),'erro_tipo':result.get('erro_tipo')},ensure_ascii=True),flush=True)


if __name__=='__main__':
    import sys
    inspect(Path(sys.argv[1]))
