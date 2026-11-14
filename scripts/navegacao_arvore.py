"""Resolve caminho por nomes; expande somente pais recolhidos, sem retry de acao."""
from ctypes import byref
import time
from modal_concorrente import critical,log


class CaminhoAusente(LookupError):
    pass


def localizar_expandindo(driver,path,events,timeout=5):
    from pyjab.jabelement import JABElement
    from pyjab.accessibleinfo import AccessibleActions
    import win32gui as g
    import win32process
    if len(path)<2:raise ValueError('caminho_incompleto')
    _,pid=win32process.GetWindowThreadProcessId(driver.hwnd)
    def no_modal():
        found=[]
        def see(h,_):
            if g.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1]==pid and g.GetClassName(h) in {'SunAwtDialog','#32770'}:found.append(h)
        g.EnumWindows(see,None)
        if found:raise RuntimeError('modal_inesperada_na_navegacao')
    def release(held):
        for el in reversed(held):el.release_jabelement()
    def resolve(prefix):
        # Novo contexto de janela e nova arvore apos cada expansao/consulta.
        held=[];count=0
        try:
            context,vmid=driver._get_accessible_context_from_hwnd(driver.hwnd)
            if not context.value or vmid!=driver.vmid:raise RuntimeError('contexto_java_mudou')
            root=JABElement(driver.bridge,driver.hwnd,vmid,context);held.append(root)
            def children(el):
                n=el.children_count
                if n>700:raise RuntimeError('limite_filhos')
                result=[]
                for i in range(n):
                    ctx=driver.bridge.getAccessibleChildFromContext(vmid,el.accessible_context,i)
                    if ctx:
                        c=JABElement(driver.bridge,driver.hwnd,vmid,ctx);held.append(c);result.append(c)
                return result
            def find_tree(el,scope=False,depth=0):
                nonlocal count
                count+=1
                if count>900 or depth>24:raise RuntimeError('limite_arvore')
                role=el.role_en_us
                scope=scope or (role=='page tab' and el.name=='Relatórios')
                if role=='tree':return [el] if scope else []
                if role in {'text','list','table','menu bar','tool bar','password text'}:return []
                result=[]
                for c in children(el):result.extend(find_tree(c,scope,depth+1))
                return result
            trees=find_tree(root)
            if len(trees)!=1:raise RuntimeError('arvore_ausente_ambigua')
            tree=trees[0];node=tree;parent=tree
            for segment in prefix:
                parent=node
                candidates=[c for c in children(parent) if c.name==segment]
                if not candidates:raise CaminhoAusente('segmento_ausente')
                if len(candidates)>1:raise RuntimeError('segmento_ambiguo')
                node=candidates[0]
            return node,parent,tree,held
        except Exception:
            release(held);raise
    steps=[]
    for depth,name in enumerate(path[:-1],1):
        no_modal()
        node,parent,tree,held=critical(events,'resolver_pai_'+str(depth),lambda:resolve(path[:depth]))
        try:
            states=node.states_en_us
            entry={'nome':name,'caminho':path[:depth],'estados_iniciais':states,
                   'expandido_inicial':'expanded' in states,'acao_executada':False}
            steps.append(entry)
            if 'expanded' in states:
                log(events,'pai_ja_expandido_sem_acao',caminho=path[:depth]);continue
            if 'expandable' not in states or 'collapsed' not in states:raise RuntimeError('pai_sem_estado_expansivel_recolhido')
            info=AccessibleActions()
            if node.accessible_action:driver.bridge.getAccessibleActions(driver.vmid,node.accessible_context,byref(info))
            actions=[info.actionInfo[i].name for i in range(min(info.actionsCount,32))]
            entry['acoes_disponiveis']=actions
            if 'toggleexpand' not in actions:raise RuntimeError('sem_toggleexpand_nao_usar_clique_de_linha')
            entry.update(metodo='toggleexpand',acao_executada=True)
            log(events,'antes_expansao_unica',caminho=path[:depth],metodo='toggleexpand')
            # expand() rele o estado e nao alterna se ja estiver expanded.
            critical(events,'node.expand_simulate_False',lambda:node.expand(simulate=False))
        finally:release(held)
        deadline=time.monotonic()+timeout;confirmed=False
        while time.monotonic()<deadline:
            driver._pump_messages();no_modal()
            try:
                current,_,_,fresh=resolve(path[:depth])
            except LookupError:
                time.sleep(.1);continue  # Apenas leitura; nenhuma nova acao.
            try:
                confirmed='expanded' in current.states_en_us
                if confirmed:
                    entry['estados_finais']=current.states_en_us
                    log(events,'expansao_confirmada_referencias_novas',caminho=path[:depth]);break
            finally:release(fresh)
            time.sleep(.1)
        if not confirmed:raise TimeoutError('expansao_nao_confirmada')
    node,parent,tree,held=resolve(path)
    log(events,'relatorio_localizado_sem_abrir',caminho=path,expansoes=sum(s['acao_executada'] for s in steps))
    return node,parent,tree,held,steps
