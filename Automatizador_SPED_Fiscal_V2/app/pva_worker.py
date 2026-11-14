"""Inspecao da arvore somente de leitura; nenhum clique, expansao ou selecao."""
import json
import logging
from pathlib import Path
import re
import sys
import tomllib
import time

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
from execucao_runtime import RESOURCES
BASE=RESOURCES


def locate_report_tree(root,children):
    def find(el,scope=False,depth=0):
        if depth>24:raise RuntimeError('limite_profundidade')
        role=el.role_en_us
        scope=scope or (role=='page tab' and el.name=='Relatórios')
        if role=='tree':return el if scope else None
        if role in {'text','table','list','menu bar','tool bar'}:return None
        for child in children(el):
            result=find(child,scope,depth+1)
            if result is not None:return result
        return None
    found=find(root)
    if found is None:raise RuntimeError('arvore_ausente_ambigua')
    return found


def inspect(expand_categories=False):
    from modal_concorrente import state
    from acessar_lista_escrituracoes import dialogs
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    def block(self): raise RuntimeError('alteracao_ambiente_bloqueada')
    Service.__wrapped__.enable_bridge=block
    d=None;held=[];paths=[];trees=[];count=0;unnamed=0;observations=[]
    try:
        hwnd,pid,_=state()
        if dialogs(pid): raise RuntimeError('modal_aberta')
        cfg=tomllib.loads((BASE/'config/diagnostico.toml').read_text('utf-8'))
        d=JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5)
        def children(el):
            nonlocal count
            result=[]
            for i in range(el.children_count):
                count+=1
                if count>1800: raise RuntimeError('limite_arvore')
                ctx=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
                if ctx:
                    c=JABElement(d.bridge,hwnd,d.vmid,ctx);held.append(c);result.append(c)
            return result
        expanded=[]
        if expand_categories:
            for step in range(35):
                if dialogs(pid):raise RuntimeError('modal_aberta')
                tree=locate_report_tree(d.root_element,children)
                candidate=[]
                def find_collapsed(el,path=()):
                    if candidate:return
                    for child in children(el):
                        name=child.name
                        if not name:continue
                        current=path+(name,)
                        if child.children_count and 'collapsed' in child.states_en_us:
                            candidate.append((child,current));return
                        if child.children_count:find_collapsed(child,current)
                        if candidate:return
                find_collapsed(tree)
                if not candidate:break
                node,path=candidate[0]
                if path in expanded:raise RuntimeError('expansao_nao_confirmada')
                node.expand(simulate=False);expanded.append(path)
                until=time.monotonic()+5
                while time.monotonic()<until:
                    d._pump_messages()
                    if dialogs(pid):raise RuntimeError('modal_aberta')
                    if 'expanded' in node.states_en_us:break
                    time.sleep(.1)
                else:raise TimeoutError('expansao_nao_confirmada')
            else:raise RuntimeError('limite_arvore')
        tree=locate_report_tree(d.root_element,children)
        def nodes(el,path,depth=0):
            nonlocal unnamed
            if depth>20: raise RuntimeError('limite_profundidade')
            for c in children(el):
                name=c.name
                observations.append({'profundidade':len(path),'papel':c.role_en_us,
                    'nome_vazio':not bool(name),'descricao_tamanho':len(c.description),'filhos':c.children_count,
                    'exibido':'showing' in c.states_en_us})
                if not name:
                    unnamed+=1
                    continue # Nao inventar caminho para no sem nome acessivel.
                if re.search(r'\d{14}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',name):
                    raise RuntimeError('nome_nao_seguro')
                current=path+[name]
                if c.children_count: nodes(c,current,depth+1)
                else: paths.append(current)
        nodes(tree,[])
        if dialogs(pid): raise RuntimeError('modal_aberta')
        if not paths:raise RuntimeError('arvore_ausente_ambigua')
        return {'sucesso':True,'somente_leitura_de_relatorios':True,'relatorios_ativados':0,
            'categorias_expandidas':[list(p) for p in expanded],'caminhos':paths,'nos_sem_nome_omitidos':unnamed}
    except Exception as exc:
        import traceback
        result={'sucesso':False,'erro_tipo':type(exc).__name__,
            'pilha':[{'funcao':f.name,'linha':f.lineno} for f in traceback.extract_tb(exc.__traceback__)]}
        if str(exc) in {'limite_arvore','limite_profundidade','arvore_ausente_ambigua','nome_nao_seguro','modal_aberta','pva_ausente_ambiguo','expansao_nao_confirmada'}:
            result['motivo']=str(exc)
        return result
    finally:
        for c in reversed(held):
            try:c.release_jabelement()
            except Exception:pass
        if d:d.detach()


if __name__=='__main__':
    (Path(sys.argv[1])/'resultado.json').write_text(json.dumps(inspect('--expandir-categorias' in sys.argv),ensure_ascii=False,indent=2),encoding='utf-8')
