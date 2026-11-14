"""Clique fisico unico no Salvar atual; B apenas reconhece e inspeciona."""
import ctypes
from datetime import datetime
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import tomllib

from modal_concorrente import ROOT, log, critical, state, worker_b


def worker_a(run,require_subreports=False):
    import win32gui as g
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from preparar_salvar_fisico import preparar_alvo
    logging.disable(logging.CRITICAL)
    events=run/'A.eventos.jsonl'
    result={'cliques_tentados':0,'metodo':'JABElement.click(simulate=True)','doAccessibleActions_usado':False}
    def record():
        with (run/'A.resultado.json').open('w',encoding='utf-8') as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.flush()
            import os
            os.fsync(f.fileno())
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    held=[];d=None
    try:
        hwnd,pid,baseline=state()
        result.update(hwnd=hwnd,pid_pva=pid)
        if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in baseline):raise RuntimeError('modal_ja_aberta')
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        d=critical(events,'JABDriver.principal',lambda:JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5))
        if g.IsIconic(hwnd):critical(events,'restaurar_pva',lambda:g.ShowWindow(hwnd,9))
        def foreground():
            if g.GetForegroundWindow()==hwnd:return
            try:g.SetForegroundWindow(hwnd)
            except g.error:
                import win32api
                current=win32api.GetCurrentThreadId()
                other=win32process.GetWindowThreadProcessId(g.GetForegroundWindow())[0]
                attached=False
                try:
                    if current!=other:
                        win32process.AttachThreadInput(current,other,True);attached=True
                    g.BringWindowToTop(hwnd);g.SetForegroundWindow(hwnd)
                finally:
                    if attached:win32process.AttachThreadInput(current,other,False)
        critical(events,'ativar_pva_sem_teclas',foreground)
        time.sleep(.3)
        found=[];count=0
        def walk(el,depth=0):
            nonlocal count
            count+=1
            if count>900 or depth>24:raise RuntimeError('limite_inspecao')
            role=el.role_en_us
            if role=='push button' and 'showing' in el.states_en_us and (el.name.strip()=='Salvar' or el.description.strip()=='Salvar'):found.append(el)
            if role in {'tree','text','table','list','password text','menu bar'}:return
            for i in range(min(el.children_count,700)):
                ctx=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
                if ctx:
                    child=JABElement(d.bridge,hwnd,d.vmid,ctx);held.append(child);walk(child,depth+1)
        critical(events,'localizar_salvar_visualizador',lambda:walk(d.root_element))
        result['botoes_salvar_visiveis_encontrados']=len(found)
        record()
        if len(found)!=1:raise RuntimeError('salvar_nao_univoco')
        button=found[0]
        if require_subreports:
            from subrelatorios import garantir_subrelatorios
            result['subrelatorios_antes_abrir_salvar']=critical(events,'confirmar_subrelatorios_imediatamente_antes_exportar',
                lambda:garantir_subrelatorios(d,events,allow_change=False))
            record()
        result['alvo']=critical(events,'preparar_alvo_recalcular_limites',lambda:preparar_alvo(d,button))
        if state()[2]-baseline:raise RuntimeError('janela_inesperada')
        with (run/'clique_unico.lock').open('x',encoding='utf-8') as f:f.write('uma tentativa')
        result['cliques_tentados']=1;record()
        critical(events,'button.click_simulate_True',lambda:button.click(simulate=True))
        result['clique_retornou']=True;record()
        # Mantem a bridge viva e sua thread atendida ate B concluir.
        critical(events,'aguardar_B_mantendo_bridge',lambda:wait_signal(d,run/'B_concluido.signal'))
    except Exception as exc:
        import traceback
        result['erro_tipo']=type(exc).__name__
        log(events,'erro_A',tipo=type(exc).__name__,pilha=[{'arquivo':Path(x.filename).name,'funcao':x.name,'linha':x.lineno} for x in traceback.extract_tb(exc.__traceback__)])
    finally:
        record()
        for el in reversed(held):critical(events,'liberar_elemento',el.release_jabelement)
        if d:critical(events,'driver.detach',d.detach)
        log(events,'A_solicita_saida_normal')


def wait_signal(driver,signal):
    while not signal.exists():
        driver._pump_messages();time.sleep(.05)


def supervisor():
    import win32gui as g
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=logs/('salvar_fisico_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    events=run/'supervisor.jsonl'
    result={'sucesso':False,'A_encerrado_forcadamente':False,'salvamento_confirmado':False}
    a=b=None;streams=[];start=time.monotonic()
    props=Path.home()/'.accessibility.properties';before=props.read_bytes() if props.exists() else None
    retry=len(sys.argv)==3 and sys.argv[1]=='--nova-autorizacao-sem-clique-anterior'
    def launch(mode,extra=[]):
        out=(run/(mode+'.stdout.txt')).open('w');err=(run/(mode+'.stderr.txt')).open('w');streams.extend([out,err])
        p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(run),*extra],
                           stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        log(events,'iniciou_worker',modo=mode,pid_worker=p.pid)
        return p
    try:
        main,pid,baseline=state()
        hung=bool(ctypes.windll.user32.IsHungAppWindow(main))
        result.update(pid_pva=pid,hwnd_principal=main,pva_nao_sinalizado_como_travado=not hung)
        if hung:raise RuntimeError('pva_nao_responde')
        if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in baseline):raise RuntimeError('modal_inicial_nao_reabrir')
        if retry:
            previous=Path(sys.argv[2]).resolve()
            if previous.parent!=logs.resolve():raise RuntimeError('pasta_anterior_invalida')
            prior=json.loads((previous/'A.resultado.json').read_text('utf-8'))
            if prior.get('cliques_tentados')!=0 or (previous/'clique_unico.lock').exists():raise RuntimeError('clique_anterior_nao_pode_ser_repetido')
            result['nova_autorizacao_usuario']=True
            result['teste_anterior_sem_clique']=str(previous)
            with (previous/'nova_autorizacao_utilizada.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        else:
            with (logs/'salvar_fisico_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        a=launch('A');result['pid_A']=a.pid
        save=None;deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            current=state()
            if current[:2]!=(main,pid):raise RuntimeError('pva_mudou')
            new=current[2]-baseline
            expected={h for h in new if g.GetClassName(h)=='SunAwtDialog' and g.GetWindowText(h)=='Salvar'}
            if new-expected or len(expected)>1:raise RuntimeError('janela_inesperada')
            if len(expected)==1:save=next(iter(expected));break
            if a.poll() is not None:raise RuntimeError('A_finalizou_sem_dialogo')
            time.sleep(.05)
        if save is None:raise TimeoutError('prazo_A')
        result.update(hwnd_salvar=save,modal_detectada=True,A_vivo_ao_iniciar_B=a.poll() is None)
        log(events,'modal_detectada',hwnd=save)
        b=launch('B',[str(save),str(pid)]);result['pid_B']=b.pid
        deadline=time.monotonic()+20
        while b.poll() is None and time.monotonic()<deadline:
            if state()[2]-(baseline|{save}):raise RuntimeError('janela_inesperada_durante_B')
            time.sleep(.05)
        if b.poll() is None:
            b.kill();b.wait(timeout=5);result['B_timeout_encerrado']=True
        result.update(B_exit_code=b.returncode,A_vivo_apos_B=a.poll() is None)
        log(events,'B_finalizou',exit_code=b.returncode)
        if (run/'B.resultado.json').exists():
            br=json.loads((run/'B.resultado.json').read_text('utf-8'));result['resultado_B']=br
            result['sucesso']=bool(br.get('isJavaWindow') and br.get('getAccessibleContextFromHWND') and br.get('campo_nome_identificado') and b.returncode==0)
        (run/'B_concluido.signal').write_text('permitir saida normal de A',encoding='utf-8')
        try:a.wait(timeout=8)
        except subprocess.TimeoutExpired:result['A_timeout_saida_preservado']=True
        result.update(A_permanece_vivo=a.poll() is None,A_exit_code=a.poll())
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        log(events,'erro_supervisor',tipo=type(exc).__name__)
    finally:
        if b is not None and b.poll() is None:
            b.kill();b.wait(timeout=5);result['B_encerrado_por_interrupcao']=True
        if a is not None:
            (run/'B_concluido.signal').write_text('B nao esta em execucao',encoding='utf-8')
            result['A_permanece_vivo']=a.poll() is None
        result.update(total_segundos=round(time.monotonic()-start,4),
                      configuracao_preservada=before==(props.read_bytes() if props.exists() else None))
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        for f in streams:f.close()
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        mode,run=sys.argv[2],Path(sys.argv[3])
        if mode=='A':worker_a(run)
        else:worker_b(run,int(sys.argv[4]),int(sys.argv[5]))
    else:supervisor()
