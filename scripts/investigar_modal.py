"""Supervisor/worker para diagnostico limitado; nao confirma salvamento."""
from datetime import datetime, timezone
import faulthandler
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'saida/TESTE_FICTICIO/teste_processos_separados.pdf'


def event(path, kind, call, **extra):
    row = dict(timestamp=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
               evento=kind, chamada=call, **extra)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(row, ensure_ascii=True), flush=True)


def critical(path, name, fn):
    event(path, 'antes', name)
    value = fn()
    event(path, 'depois', name)
    return value


def windows():
    import win32gui as gui
    import win32process
    visible = []
    gui.EnumWindows(lambda h, _: visible.append(h) if gui.IsWindowVisible(h) else None, None)
    roots = [h for h in visible if gui.GetWindowText(h).startswith('Sped Fiscal - EFD ICMS/IPI')]
    if len(roots)!=1:
        raise RuntimeError('pva_ausente_ou_ambiguo')
    _, pid = win32process.GetWindowThreadProcessId(roots[0])
    owned = {h for h in visible if win32process.GetWindowThreadProcessId(h)[1]==pid}
    dialogs = [h for h in owned if gui.GetClassName(h) in {'SunAwtDialog','#32770'}]
    saves = [h for h in dialogs if gui.GetWindowText(h).casefold()=='salvar']
    if len(saves)>1 or len(dialogs)!=len(saves):
        raise RuntimeError('salvar_ausente_ambiguo_ou_dialogo_inesperado')
    return roots[0], saves[0] if saves else None, pid, owned


def worker(mode, path):
    import logging
    logging.disable(logging.CRITICAL)
    stack = path.with_suffix('.stack.txt').open('w',encoding='utf-8')
    faulthandler.enable(stack)
    faulthandler.dump_traceback_later(12, file=stack)
    main, save, pid, baseline = windows()
    event(path,'estado','janelas_iniciais',pva_pid=pid,main_hwnd=main,save_hwnd=save)
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from pyjab.common.win32utils import Win32Utils
    # Instrumentacao apenas em memoria; nao modifica pacotes instalados.
    def wrap(cls, name):
        original=getattr(cls,name)
        def traced(*args, **kwargs):
            return critical(path, cls.__name__+'.'+name, lambda: original(*args,**kwargs))
        setattr(cls,name,traced)
    for name in ['init_jab','_pump_messages','_get_accessible_context_from_hwnd','_is_java_window']:
        wrap(JABDriver,name)
    for name in ['load_library','init_bridge']:
        wrap(Service.__wrapped__,name)
    original_load=Service.__wrapped__.load_library
    def load(self,*args,**kwargs):
        lib=original_load(self,*args,**kwargs)
        for name in ['Windows_run','getAccessibleContextFromHWND']:
            original=getattr(lib,name)
            def traced(*a, _name=name, _original=original):
                return critical(path,'bridge.'+_name,lambda:_original(*a))
            setattr(lib,name,traced)
        return lib
    Service.__wrapped__.load_library=load
    def block(self):
        raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
    drivers=[]
    held=[]
    try:
        if mode=='A':
            if save is not None:
                raise RuntimeError('salvar_ja_aberto_nao_reabrir')
            d=critical(path,'JABDriver.main',lambda:JABDriver(hwnd=main,bridge_dll=cfg['bridge_dll'],timeout=5))
            drivers.append(d)
            def children(el):
                count=critical(path,'element.children_count',lambda:el.children_count)
                if count>700:raise RuntimeError('limite_filhos')
                out=[]
                for i in range(count):
                    ctx=critical(path,'bridge.getAccessibleChildFromContext',lambda:d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i))
                    if ctx:
                        child=critical(path,'JABElement.__init__',lambda:JABElement(d.bridge,main,d.vmid,ctx))
                        held.append(child);out.append((i,child))
                return out
            def scan(el,kind,scope=False,depth=0):
                if depth>24:raise RuntimeError('limite_profundidade')
                role=el.role_en_us
                scope=scope or (role=='page tab' and el.name=='Relatórios')
                found=[]
                if kind=='tree' and role=='tree' and scope:found.append(el)
                if kind=='save' and role=='push button' and 'showing' in el.states_en_us and (el.name=='Salvar' or el.description=='Salvar'):found.append(el)
                if role in {'tree','text','list','table','menu bar','password text'}:return found
                for _,child in children(el):found.extend(scan(child,kind,scope,depth+1))
                return found
            trees=critical(path,'localizar_arvore',lambda:scan(d.root_element,'tree'))
            if len(trees)!=1:raise RuntimeError('arvore_ambigua')
            parent=trees[0]
            target=['Escrituração Fiscal','Relatórios de Registros Fiscais','Apuração do ICMS','Operações Próprias']
            for pos,name in enumerate(target):
                found=[(i,c) for i,c in children(parent) if c.name==name]
                if len(found)!=1:raise RuntimeError('caminho_ambiguo')
                index,node=found[0]
                if not {'visible','showing'}.issubset(node.states_en_us):raise RuntimeError('no_nao_visivel')
                if pos<3:
                    if 'expanded' not in node.states_en_us:raise RuntimeError('pai_recolhido')
                    parent=node
            if not parent.accessible_selection:raise RuntimeError('pai_sem_selecao')
            critical(path,'bridge.addAccessibleSelectionFromContext',lambda:d.bridge.addAccessibleSelectionFromContext(d.vmid,parent.accessible_context,index))
            if 'selected' not in node.states_en_us:raise RuntimeError('selecao_nao_confirmada')
            for _ in range(20):
                critical(path,'aguardar_visualizador.pump',d._pump_messages)
                if windows()[1] is not None:raise RuntimeError('dialogo_inesperado')
                time.sleep(.25)
            saves=critical(path,'localizar_salvar_visualizador',lambda:scan(d.root_element,'save'))
            event(path,'estado','salvar_visualizador',quantidade=len(saves),
                  habilitado=len(saves)==1 and 'enabled' in saves[0].states_en_us)
            if len(saves)!=1 or 'enabled' not in saves[0].states_en_us:raise RuntimeError('salvar_nao_univoco')
            # Trava desta investigacao: sem repeticao de abertura em nova execucao.
            with (ROOT/'logs/investigar_modal_A_acionado.lock').open('x',encoding='utf-8') as f:f.write(str(path))
            critical(path,'botao_visualizador._do_accessible_action',lambda:saves[0]._do_accessible_action('click'))
            for _ in range(20):
                critical(path,'pos_modal.driver._pump_messages',d._pump_messages)
                save=critical(path,'pos_modal.enumerar_janelas',lambda:windows()[1])
                if save is not None:break
                time.sleep(.25)
            if save is None:raise RuntimeError('salvar_nao_abriu')
            event(path,'resultado','processo_A_abriu_salvar',save_hwnd=save)
            # Reproduz somente a segunda conexao do fluxo anterior, sem preencher/salvar.
            second=critical(path,'JABDriver.segundo_driver_modal',lambda:JABDriver(hwnd=save,bridge_dll=cfg['bridge_dll'],timeout=5))
            drivers.append(second)
            event(path,'resultado','segunda_conexao_retornou')
            return
        if save is None:
            raise RuntimeError('salvar_ausente')
        if mode=='probe':
            drivers.append(critical(path,'JABDriver.main_com_modal_aberta',lambda:JABDriver(
                hwnd=main,bridge_dll=cfg['bridge_dll'],timeout=5)))
        d=critical(path,'JABDriver.dialogo',lambda:JABDriver(hwnd=save,bridge_dll=cfg['bridge_dll'],timeout=5))
        drivers.append(d)
        found=[]
        visited=0
        def walk(el,depth=0):
            nonlocal visited
            visited+=1
            if depth>16 or visited>240:
                raise RuntimeError('limite_inspecao')
            role=critical(path,'element.role_en_us',lambda:el.role_en_us)
            if role=='text':
                name=critical(path,'element.name',lambda:el.name)
                if name.strip().casefold()=='nome do arquivo:':
                    found.append(el)
            if role in {'text','password text','list','table','tree'}:
                return
            count=critical(path,'element.children_count',lambda:el.children_count)
            for i in range(count):
                context=critical(path,'bridge.getAccessibleChildFromContext',lambda:d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i))
                if context:
                    child=critical(path,'JABElement.__init__',lambda:JABElement(d.bridge,save,d.vmid,context))
                    held.append(child)
                    walk(child,depth+1)
        critical(path,'inspecionar_dialogo',lambda:walk(d.root_element))
        if mode=='probe':
            event(path,'resultado','probe_somente_leitura',campos=len(found))
            return
        if len(found)!=1:
            raise RuntimeError('campo_nao_univoco')
        field=found[0]
        states=critical(path,'field.states_en_us',lambda:field.states_en_us)
        if not {'enabled','editable','showing'}.issubset(states):
            raise RuntimeError('campo_nao_editavel')
        if DEST.exists():
            raise RuntimeError('destino_ja_existe')
        if windows()[3]-baseline:
            raise RuntimeError('janela_inesperada')
        critical(path,'field.send_text',lambda:field.send_text(str(DEST),simulate=False,wait_for_text_update=False))
        matches=critical(path,'field.text_readback',lambda:field.text)==str(DEST)
        event(path,'resultado','processo_B',preenchimento_confirmado=matches,
              janela_salvar_aberta=True,arquivo_criado=DEST.exists())
    finally:
        for el in reversed(held):
            critical(path,'element.release',lambda:el.release_jabelement())
        for d in reversed(drivers):
            critical(path,'driver.detach',d.detach)
        faulthandler.cancel_dump_traceback_later()
        stack.close()


def supervisor():
    logs=ROOT/'logs'
    logs.mkdir(exist_ok=True)
    run=logs/('modal_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    run.mkdir()
    props=Path.home()/'.accessibility.properties'
    before=props.read_bytes() if props.exists() else None
    main,save,pid,_=windows()
    summary={'processo_A':'dispensado_dialogo_ja_aberto' if save else 'executar_uma_vez',
             'pva_pid':pid,'save_hwnd':save,'workers':[]}
    # Probe de leitura somente: main sob modal e segunda conexao. B usa sessao nova.
    for mode in (['probe','B'] if save else ['A','B']):
        path=run/(mode+'.jsonl')
        with (run/(mode+'.stdout.jsonl')).open('w',encoding='utf-8') as out, (run/(mode+'.stderr.txt')).open('w',encoding='utf-8') as err:
            p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(path)],
                               stdout=out,stderr=err,cwd=ROOT)
            timeout=False
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                timeout=True
                p.kill()  # Apenas o worker criado por este supervisor, nunca o PVA.
                p.wait(timeout=5)
            summary['workers'].append({'modo':mode,'pid':p.pid,'exit_code':p.returncode,'timeout':timeout})
        if path.exists():
            rows=[json.loads(line) for line in path.read_text('utf-8').splitlines()]
            pending=[]
            for row in rows:
                if row['evento']=='antes': pending.append(row['chamada'])
                elif row['evento']=='depois' and pending and pending[-1]==row['chamada']:pending.pop()
            summary['workers'][-1].update(chamadas_pendentes=pending,
                resultados=[r for r in rows if r['evento']=='resultado'])
        # Reconfirma a mesma janela/processo sem repetir acao de interface.
        observed=windows()
        if mode=='A' and save is None:
            save=observed[1]
            summary['save_hwnd']=save
        if observed[:3]!=(main,save,pid) or save is None:
            summary['interrupcao']='janelas_mudaram'
            break
    summary['configuracao_preservada']=before==(props.read_bytes() if props.exists() else None)
    summary['arquivo_criado']=DEST.exists()
    (run/'resultado.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pasta_logs':str(run),**summary},ensure_ascii=True),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        try:
            worker(sys.argv[2],Path(sys.argv[3]))
        except Exception as exc:
            import traceback
            frames=traceback.extract_tb(exc.__traceback__)
            event(Path(sys.argv[3]),'erro','worker',tipo=type(exc).__name__,
                  pilha=[{'funcao':f.name,'linha':f.lineno,'arquivo':Path(f.filename).name} for f in frames])
            sys.exit(1)
    else:
        supervisor()
