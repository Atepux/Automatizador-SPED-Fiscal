"""Inspecao e ativacao unica do no autorizado. Nunca aciona Salvar."""
from datetime import datetime, timezone
from ctypes import byref
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import tomllib

ROOT=Path(__file__).resolve().parents[1]
TARGET=['Escrituração Fiscal','Relatórios de Registros Fiscais','Apuração do ICMS','Operações Próprias']


def worker(mode, output, open_dialog=False, lock_path=None, hold_signal=None, require_subreports=False,auto_expand=False,receipt_wait=None):
    import win32gui as gui
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from pyjab.accessibleinfo import AccessibleActions
    logging.disable(logging.CRITICAL)
    result={'inicio_utc':datetime.now(timezone.utc).isoformat(),'modo':mode,'caminho':TARGET,
            'cliques_tentados':0,'sucesso':False}
    started=time.monotonic()
    def record(stage):
        result['etapa']=stage
        result['decorrido_segundos']=round(time.monotonic()-started,4)
        result['atualizacao_utc']=datetime.now(timezone.utc).isoformat()
        with output.open('w',encoding='utf-8') as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.flush()
            import os
            os.fsync(f.fileno())
        with output.with_suffix('.eventos.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'etapa':stage,'timestamp':result['atualizacao_utc'],
                                'decorrido_segundos':result['decorrido_segundos']})+'\n')
            f.flush();os.fsync(f.fileno())
    def stop(reason):
        result['interrupcao']=reason
        raise RuntimeError(reason)
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    props=Path.home()/'.accessibility.properties'
    before=props.read_bytes() if props.exists() else None
    d=None;held=[]
    try:
        record('identificar_pva')
        def windows():
            out=[]
            gui.EnumWindows(lambda h,_:out.append(h) if gui.IsWindowVisible(h) else None,None)
            return out
        roots=[h for h in windows() if gui.GetWindowText(h).startswith('Sped Fiscal - EFD ICMS/IPI')]
        if len(roots)!=1:stop('pva_ausente_ambiguo')
        hwnd=roots[0];_,pid=win32process.GetWindowThreadProcessId(hwnd)
        def owned():return {h for h in windows() if win32process.GetWindowThreadProcessId(h)[1]==pid}
        baseline=owned()
        if any(gui.GetClassName(h) in {'SunAwtDialog','#32770'} for h in baseline):stop('dialogo_aberto')
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        record('conectar')
        d=JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5)
        result.update(pid=pid,hwnd=hwnd)
        def children(el):
            if el.children_count>700:stop('limite_filhos')
            out=[]
            for i in range(el.children_count):
                c=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
                if c:
                    child=JABElement(d.bridge,hwnd,d.vmid,c);held.append(child);out.append((i,child))
            return out
        def scan(kind):
            out=[];count=0
            def walk(el,scope=False,depth=0):
                nonlocal count
                count+=1
                if count>900 or depth>24:stop('limite_inspecao')
                role=el.role_en_us
                scope=scope or (role=='page tab' and el.name=='Relatórios')
                if kind=='tree' and role=='tree' and scope:out.append(el)
                if kind=='save' and role=='push button' and 'showing' in el.states_en_us and (el.name.strip()=='Salvar' or el.description.strip()=='Salvar'):out.append(el)
                if role in {'tree','text','password text','list','table','menu bar'}:return
                for _,c in children(el):walk(c,scope,depth+1)
            walk(d.root_element)
            return out
        record('resolver_caminho')
        if auto_expand:
            from navegacao_arvore import localizar_expandindo
            node,parent,tree,fresh,steps=localizar_expandindo(d,TARGET,output.with_suffix('.navegacao.jsonl'))
            held.extend(fresh);trees=[tree];result['navegacao_pais']=steps
            if not {'visible','showing'}.issubset(node.states_en_us):stop('relatorio_nao_visivel_apos_expansao')
        else:
            trees=scan('tree')
            if len(trees)!=1:stop('arvore_ambigua')
            parent=trees[0]
            for pos,name in enumerate(TARGET):
                found=[c for _,c in children(parent) if c.name==name]
                if len(found)!=1:stop('segmento_ausente_ambiguo')
                node=found[0]
                if not {'visible','showing'}.issubset(node.states_en_us):stop('no_nao_visivel')
                if pos<len(TARGET)-1:
                    if 'expanded' not in node.states_en_us:stop('pai_recolhido')
                    parent=node
        def actions(el):
            if not el.accessible_action:return []
            info=AccessibleActions()
            d.bridge.getAccessibleActions(d.vmid,el.accessible_context,byref(info))
            return [info.actionInfo[i].name for i in range(min(info.actionsCount,32))]
        result.update(acoes_no=actions(node),acoes_pai=actions(parent),acoes_arvore=actions(trees[0]),
                      estados_no=node.states_en_us,estados_arvore=trees[0].states_en_us,
                      bounds_java=node.bounds)
        saves=scan('save')
        result['salvar_disponivel_antes']=len(saves)==1 and 'enabled' in saves[0].states_en_us
        record('inspecao_concluida')
        if mode=='inspect':return
        # Sem acao Java de ativacao e sem binding de teclado confirmado: clique dinamico.
        if result['acoes_no']:stop('acoes_existentes_revisar_antes_de_clique_fisico')
        # Evita d.focus(): esta versao pode enviar espaco a janela anterior.
        if gui.IsIconic(hwnd):
            gui.ShowWindow(hwnd,9)  # SW_RESTORE; nao altera empresa/relatorio.
        if gui.GetForegroundWindow()!=hwnd:
            try:
                gui.SetForegroundWindow(hwnd)
            except gui.error:
                # A recusa de foco nao executa clique. Vincula temporariamente
                # as filas de entrada e sempre desfaz o vinculo, sem enviar teclas.
                import win32api
                current=win32api.GetCurrentThreadId()
                foreground=gui.GetForegroundWindow()
                other=win32process.GetWindowThreadProcessId(foreground)[0]
                attached=False
                try:
                    if current!=other:
                        win32process.AttachThreadInput(current,other,True)
                        attached=True
                    gui.BringWindowToTop(hwnd)
                    gui.SetForegroundWindow(hwnd)
                finally:
                    if attached:win32process.AttachThreadInput(current,other,False)
        time.sleep(.3)
        d._pump_messages()
        if gui.GetForegroundWindow()!=hwnd:stop('pva_nao_esta_em_primeiro_plano')
        if owned()-baseline:stop('janela_inesperada_antes_clique')
        bounds=node.bounds
        if bounds['width']<=0 or bounds['height']<=0 or bounds['x']<0 or bounds['y']<0:stop('bounds_invalidos')
        point=node._physical_point(*node._click_point())
        under=gui.WindowFromPoint(point)
        if gui.GetAncestor(under,2)!=hwnd and under!=hwnd:stop('ponto_fora_da_janela_pva')
        result.update(bounds_java=bounds,ponto_fisico_dinamico=list(point),
                      metodo='JABElement.click(simulate=True)',cliques_tentados=1)
        with (lock_path or ROOT/'logs/ativacao_operacoes_clique.lock').open('x',encoding='utf-8') as f:f.write(str(output))
        record('antes_clique_unico')
        node.click(simulate=True)
        record('depois_clique_unico')
        clicked_at=time.monotonic()
        deadline=clicked_at+(receipt_wait if receipt_wait is not None else 12)
        if receipt_wait is not None:result['prazo_recibo_monotonic']=deadline
        delay=max(2,float(cfg.get('espera_apos_abrir_relatorio_segundos',2)))
        result['espera_minima_apos_clique_segundos']=delay
        record('aguardar_carregamento_minimo_antes_de_salvar')
        ready_after=clicked_at+delay
        while time.monotonic()<ready_after:
            d._pump_messages()
            time.sleep(min(.05,max(0,ready_after-time.monotonic())))
        record('espera_minima_carregamento_concluida')
        last_windows=None
        while time.monotonic()<deadline:
            d._pump_messages()
            additional=owned()-baseline
            if additional and receipt_wait is None:stop('janela_inesperada_apos_clique')
            if receipt_wait is not None and additional!=last_windows:
                from janelas_recibo import identificar_janelas
                result.setdefault('janelas_recibo_observadas',[]).append(identificar_janelas(additional,pid))
                last_windows=additional
                record('identificar_janelas_recibo_sem_acionar')
            saves=scan('save')
            result['selected_apos']='selected' in node.states_en_us
            result['salvar_disponivel_apos']=len(saves)==1 and 'enabled' in saves[0].states_en_us
            if result['salvar_disponivel_apos'] and result['selected_apos'] and not additional:
                result['sucesso']=True
                result['mudanca_visualizador_comprovada']=not result['salvar_disponivel_antes']
                break
            time.sleep(min(.1 if receipt_wait is not None else .5,max(0,deadline-time.monotonic())))
        if receipt_wait is not None and not result['sucesso']:
            result['pendencia_recibo']='janela_adicional_requer_identificacao' if owned()-baseline else 'controles_nao_disponiveis_no_prazo'
            stop('recibo_nao_pronto_apos_5s')
        record('verificacao_concluida')
        if require_subreports:
            if not result['sucesso']:stop('relatorio_nao_confirmado_para_subrelatorios')
            from subrelatorios import garantir_subrelatorios
            result['subrelatorios']=garantir_subrelatorios(d,output.with_suffix('.subrelatorios.jsonl'))
            # Opcao pode reconstruir o visualizador: redescobrir Salvar.
            saves=scan('save')
            if len(saves)!=1 or 'enabled' not in saves[0].states_en_us:
                stop('salvar_indisponivel_apos_subrelatorios')
            record('subrelatorios_confirmados_salvar_disponivel')
        if open_dialog:
            if not result['sucesso']:stop('visualizador_nao_confirmado')
            if owned()-baseline:stop('janela_inesperada_antes_salvar')
            result['salvar_visualizador_tentativas']=1
            record('antes_abrir_salvar')
            saves[0]._do_accessible_action('click')
            record('depois_abrir_salvar')
            if hold_signal is not None:
                record('A_vivo_aguardando_B')
                while not hold_signal.exists():
                    d._pump_messages()
                    time.sleep(.05)
                record('B_concluido_saida_normal_solicitada')
                return
            # Nao reconecta nem bombeia mensagens sob modal. Supervisor confere
            # a janela pelo Win32 e B inicializa sua propria bridge.
            import os
            os._exit(0)
    except Exception as exc:
        result['sucesso']=False
        result['erro_tipo']=type(exc).__name__
        record('interrompido')
    finally:
        for el in reversed(held):
            try:el.release_jabelement()
            except Exception as exc:
                result['sucesso']=False
                result.setdefault('erros_liberacao',[]).append(type(exc).__name__)
        if d:
            try:d.detach()
            except Exception as exc:
                result['sucesso']=False
                result['aviso_detach']=type(exc).__name__
        result['configuracao_preservada']=before==(props.read_bytes() if props.exists() else None)
        record('finalizado')


def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'inspect'
    if mode not in {'inspect','click'}:raise ValueError('modo invalido')
    folder=ROOT/'logs';folder.mkdir(exist_ok=True)
    output=folder/('ativacao_operacoes_'+mode+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
    p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(output)])
    try:p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill();p.wait(timeout=5)
        data=json.loads(output.read_text('utf-8')) if output.exists() else {}
        data.update(timeout_externo=True,worker_encerrado=True,sucesso=False)
        output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'log':str(output),'resultado':json.loads(output.read_text('utf-8'))},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2],Path(sys.argv[3]))
    else:main()
