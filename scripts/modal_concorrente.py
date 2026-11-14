"""POC sem escrita de campos/PDF. A nunca e morto pelo supervisor."""
from ctypes import byref, c_long
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib

ROOT=Path(__file__).resolve().parents[1]


def log(path,event,**data):
    row={'timestamp_utc':datetime.now(timezone.utc).isoformat(),
         'monotonic':time.monotonic(),'pid_python':os.getpid(),'evento':event,**data}
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,ensure_ascii=True)+'\n');f.flush();os.fsync(f.fileno())


def critical(path,name,fn):
    start=time.monotonic();log(path,'antes',chamada=name)
    value=fn()
    log(path,'depois',chamada=name,segundos=round(time.monotonic()-start,6))
    return value


def state():
    import win32gui as g
    import win32process
    visible=[]
    g.EnumWindows(lambda h,_:visible.append(h) if g.IsWindowVisible(h) else None,None)
    roots=[h for h in visible if g.GetWindowText(h).startswith('Sped Fiscal - EFD ICMS/IPI')]
    if len(roots)!=1:raise RuntimeError('pva_ausente_ambiguo')
    main=roots[0];_,pid=win32process.GetWindowThreadProcessId(main)
    owned={h for h in visible if win32process.GetWindowThreadProcessId(h)[1]==pid}
    return main,pid,owned


def worker_b(run,hwnd,pid):
    import win32gui as g
    import win32process
    from pyjab.common.service import Service
    from pyjab.common.win32utils import Win32Utils
    from pyjab.common.types import JOBJECT64
    from pyjab.jabfixedfunc import JABFixedFunc
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    path=run/'B.eventos.jsonl'
    result={'somente_leitura':True,'hwnd':hwnd,'pid_pva':pid,'controles':[]}
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    bridge=None;vm=c_long();context=JOBJECT64();held=[]
    try:
        if not g.IsWindowVisible(hwnd) or win32process.GetWindowThreadProcessId(hwnd)[1]!=pid or g.GetWindowText(hwnd)!='Salvar' or g.GetClassName(hwnd)!='SunAwtDialog':
            raise RuntimeError('dialogo_nao_corresponde')
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        service=critical(path,'Service.__init__',Service)
        bridge=critical(path,'Service.load_library',lambda:service.load_library(cfg['bridge_dll']))
        critical(path,'JABFixedFunc.signatures',lambda:JABFixedFunc(bridge)._fix_bridge_functions())
        critical(path,'bridge.Windows_run',lambda:bridge.Windows_run())
        pump=Win32Utils()
        def service_initial_messages():
            deadline=time.monotonic()+1
            while time.monotonic()<deadline:
                pump.pump_messages();time.sleep(.02)
        critical(path,'inicializar_fila_mensagens_1s',service_initial_messages)
        recognized=critical(path,'bridge.isJavaWindow',lambda:bool(bridge.isJavaWindow(hwnd)))
        result['isJavaWindow']=recognized
        log(path,'resultado_isJavaWindow',valor=recognized)
        got=critical(path,'bridge.getAccessibleContextFromHWND',lambda:bool(bridge.getAccessibleContextFromHWND(hwnd,byref(vm),byref(context))))
        result.update(getAccessibleContextFromHWND=got,vmid=vm.value,contexto_nao_nulo=bool(context.value))
        log(path,'resultado_contexto',sucesso=got,vmid=vm.value,contexto_nao_nulo=bool(context.value))
        if got and context.value:
            root=critical(path,'JABElement.root',lambda:JABElement(bridge,hwnd,vm.value,context))
            held.append(root)
            safe={'Salvar','Cancelar','Salvar em:','Nome do arquivo:','Arquivos do tipo:'}
            def walk(el,depth=0):
                if depth>16 or len(result['controles'])>=180:return
                role=el.role_en_us;name=el.name
                result['controles'].append({'papel':role,'nome':name if name in safe else '[omitido]' if name else '',
                                            'estados':el.states_en_us})
                if role in {'text','list','tree','table','password text'}:return
                for i in range(min(el.children_count,180)):
                    ctx=bridge.getAccessibleChildFromContext(vm.value,el.accessible_context,i)
                    if ctx:
                        child=JABElement(bridge,hwnd,vm.value,ctx);held.append(child);walk(child,depth+1)
            critical(path,'ler_controles_sem_textos_de_campos',lambda:walk(root))
            result['campo_nome_identificado']=any(x['papel']=='text' and x['nome']=='Nome do arquivo:' for x in result['controles'])
        result['finalizado']=True
    except Exception as exc:
        import traceback
        result['erro_tipo']=type(exc).__name__
        log(path,'erro',tipo=type(exc).__name__,pilha=[{'arquivo':Path(f.filename).name,'funcao':f.name,'linha':f.lineno} for f in traceback.extract_tb(exc.__traceback__)])
    finally:
        # Persistir antes de liberar referencias: cleanup tambem pode bloquear.
        (run/'B.resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        for el in reversed(held):
            critical(path,'releaseJavaObject',el.release_jabelement)
        log(path,'B_solicita_saida_normal')


def supervise():
    import win32gui as g
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=logs/('modal_concorrente_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    path=run/'supervisor.jsonl'
    result={'A_encerrado_forcadamente':False,'B_iniciado':False,'salvamento_confirmado':False}
    a=b=None;handles=[];start=time.monotonic()
    props=Path.home()/'.accessibility.properties';before=props.read_bytes() if props.exists() else None
    def launch(mode,extra=[]):
        out=(run/(mode+'.stdout.txt')).open('w');err=(run/(mode+'.stderr.txt')).open('w');handles.extend([out,err])
        p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(run),*extra],
                           stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        log(path,'processo_iniciado',modo=mode,pid_filho=p.pid)
        return p
    try:
        main,pid,baseline=state()
        if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in baseline):raise RuntimeError('dialogo_inicial_aberto_nao_reabrir')
        with (logs/'modal_concorrente_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        result.update(pid_pva=pid,hwnd_principal=main)
        a=launch('A');result['pid_A']=a.pid
        deadline=time.monotonic()+30
        save=None
        while time.monotonic()<deadline:
            current=state()
            if current[:2]!=(main,pid):raise RuntimeError('pva_mudou')
            new=current[2]-baseline
            expected={h for h in new if g.GetClassName(h)=='SunAwtDialog' and g.GetWindowText(h)=='Salvar'}
            if new-expected or len(expected)>1:raise RuntimeError('janela_inesperada')
            if len(expected)==1:
                save=next(iter(expected));break
            if a.poll() is not None:raise RuntimeError('A_finalizou_sem_modal')
            time.sleep(.05)
        if save is None:raise TimeoutError('prazo_A_sem_modal_preservar_A')
        if a.poll() is not None:raise RuntimeError('A_nao_esta_vivo')
        result.update(hwnd_salvar=save,A_vivo_ao_iniciar_B=True)
        log(path,'modal_detectada_A_vivo',hwnd=save,pid_pva=pid)
        b=launch('B',[str(save),str(pid)]);result.update(B_iniciado=True,pid_B=b.pid)
        deadline=time.monotonic()+20;all_alive=True
        while b.poll() is None and time.monotonic()<deadline:
            all_alive=all_alive and a.poll() is None
            if state()[2]-(baseline|{save}):
                result['janela_inesperada']=True;break
            time.sleep(.05)
        if b.poll() is None:
            log(path,'encerrar_somente_B',pid_B=b.pid)
            b.kill();b.wait(timeout=5);result['B_timeout_ou_interrupcao']=True
        result.update(B_exit_code=b.returncode,A_vivo_durante_B=all_alive and a.poll() is None)
        log(path,'B_concluido',exit_code=b.returncode,A_vivo=a.poll() is None)
        if (run/'B.resultado.json').exists():result['resultado_B']=json.loads((run/'B.resultado.json').read_text('utf-8'))
        # Somente depois que B terminou solicita retorno/cleanup normal de A.
        (run/'B_concluido.signal').write_text('B terminado; permitir saida normal de A',encoding='utf-8')
        try:a.wait(timeout=8)
        except subprocess.TimeoutExpired:result['A_saida_normal_timeout']=True
        result.update(A_permanece_vivo=a.poll() is None,A_exit_code=a.poll())
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        log(path,'erro_supervisor',tipo=type(exc).__name__)
        if b is not None and b.poll() is None:
            b.kill();b.wait(timeout=5);result['B_encerrado_por_interrupcao']=True
        if a is not None:
            (run/'B_concluido.signal').write_text('B nao esta em execucao',encoding='utf-8')
            result['A_permanece_vivo']=a.poll() is None
    finally:
        result.update(duracao_total_segundos=round(time.monotonic()-start,4),
                      configuracao_preservada=before==(props.read_bytes() if props.exists() else None))
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        for f in handles:f.close()
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        mode,run=sys.argv[2],Path(sys.argv[3])
        if mode=='A':
            from ativar_operacoes_proprias import worker
            worker('click',run/'A.json',open_dialog=True,lock_path=run/'A.clique.lock',hold_signal=run/'B_concluido.signal')
        else:worker_b(run,int(sys.argv[4]),int(sys.argv[5]))
    else:supervise()
