"""Conclui somente o dialogo ja aberto, sem reabrir relatorio ou Salvar."""
from ctypes import byref,c_long
from datetime import datetime
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from modal_concorrente import ROOT, state, critical, log

DEST=ROOT/'saida/TESTE_FICTICIO/relatorio_teste_fisico.pdf'


def identificar_dialogo():
    import win32gui as g
    main,pid,owned=state()
    dialogs={h for h in owned if g.GetClassName(h) in {'SunAwtDialog','#32770'}}
    saves={h for h in dialogs if g.GetClassName(h)=='SunAwtDialog' and g.GetWindowText(h)=='Salvar'}
    if len(saves)!=1 or dialogs!=saves:raise RuntimeError('salvar_ausente_ambiguo_ou_janela_inesperada')
    return main,pid,next(iter(saves)),owned


def worker(run):
    import win32gui as g
    import pymupdf
    from pyjab.common.service import Service
    from pyjab.common.win32utils import Win32Utils
    from pyjab.common.types import JOBJECT64
    from pyjab.jabfixedfunc import JABFixedFunc
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    events=run/'worker.eventos.jsonl'
    result={'sucesso':False,'destino':str(DEST),'tentativas_confirmar_salvar':0}
    held=[]
    def record():
        with (run/'worker.resultado.json').open('w',encoding='utf-8') as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.flush()
            import os
            os.fsync(f.fileno())
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    try:
        main,pid,hwnd,baseline=critical(events,'identificar_dialogo_PVA',identificar_dialogo)
        result.update(pid_pva=pid,hwnd_salvar=hwnd)
        if DEST.exists():raise RuntimeError('destino_ja_existe')
        DEST.parent.mkdir(parents=True,exist_ok=True)
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        service=critical(events,'Service.__init__',Service)
        bridge=critical(events,'Service.load_library',lambda:service.load_library(cfg['bridge_dll']))
        critical(events,'JABFixedFunc.signatures',lambda:JABFixedFunc(bridge)._fix_bridge_functions())
        critical(events,'bridge.Windows_run',lambda:bridge.Windows_run())
        pump=Win32Utils()
        def pump_initial():
            deadline=time.monotonic()+1
            while time.monotonic()<deadline:pump.pump_messages();time.sleep(.02)
        critical(events,'fila_inicial_1s',pump_initial)
        result['isJavaWindow']=critical(events,'bridge.isJavaWindow',lambda:bool(bridge.isJavaWindow(hwnd)))
        vm=c_long();context=JOBJECT64()
        result['contexto_obtido']=critical(events,'bridge.getAccessibleContextFromHWND',lambda:bool(bridge.getAccessibleContextFromHWND(hwnd,byref(vm),byref(context))))
        if not result['isJavaWindow'] or not result['contexto_obtido'] or not context.value:raise RuntimeError('sem_contexto_java')
        root=JABElement(bridge,hwnd,vm.value,context);held.append(root)
        fields=[];buttons=[];count=0
        def walk(el,depth=0):
            nonlocal count
            count+=1
            if count>200 or depth>16:raise RuntimeError('limite_inspecao')
            role=el.role_en_us
            if role=='text' and el.name=='Nome do arquivo:':fields.append(el)
            if role=='push button' and el.name=='Salvar':buttons.append(el)
            if role in {'text','list','tree','table','password text'}:return
            for i in range(min(el.children_count,200)):
                ctx=bridge.getAccessibleChildFromContext(vm.value,el.accessible_context,i)
                if ctx:
                    child=JABElement(bridge,hwnd,vm.value,ctx);held.append(child);walk(child,depth+1)
        critical(events,'localizar_campo_e_botao',lambda:walk(root))
        if len(fields)!=1 or len(buttons)!=1:raise RuntimeError('controles_ambiguos')
        field,button=fields[0],buttons[0]
        if not {'enabled','editable','showing'}.issubset(field.states_en_us) or not {'enabled','showing'}.issubset(button.states_en_us):raise RuntimeError('controles_indisponiveis')
        def unchanged():
            if state()[:2]!=(main,pid) or state()[2]-baseline:raise RuntimeError('janela_inesperada')
        unchanged()
        if DEST.exists():raise RuntimeError('destino_passou_a_existir')
        critical(events,'field.send_text',lambda:field.send_text(str(DEST),simulate=False,wait_for_text_update=False))
        result['caminho_confirmado']=critical(events,'field.text_readback',lambda:field.text==str(DEST))
        if not result['caminho_confirmado']:raise RuntimeError('caminho_divergente')
        unchanged()
        if DEST.exists():raise RuntimeError('destino_existe_antes_confirmacao')
        with (run/'confirmacao_unica.lock').open('x',encoding='utf-8') as f:f.write('uma tentativa')
        result['tentativas_confirmar_salvar']=1;record()
        critical(events,'button.confirmar_salvar_uma_vez',lambda:button._do_accessible_action('click'))
        def wait_file():
            deadline=time.monotonic()+20;previous=None;stable=0
            while time.monotonic()<deadline:
                unchanged()
                if DEST.is_file():
                    s=DEST.stat();sig=(s.st_size,s.st_mtime_ns)
                    stable=stable+1 if s.st_size>0 and sig==previous else 0;previous=sig
                    if stable>=4 and not g.IsWindowVisible(hwnd):return
                time.sleep(.25)
            raise TimeoutError('arquivo_nao_estavel_no_prazo')
        critical(events,'aguardar_gravacao',wait_file)
        def verify():
            with pymupdf.open(DEST) as pdf:
                result.update(pdf_abre=True,paginas=pdf.page_count,tamanho_bytes=DEST.stat().st_size,
                              formato_pdf=pdf.is_pdf,reparado=pdf.is_repaired,exige_senha=bool(pdf.needs_pass))
                if not pdf.is_pdf or pdf.needs_pass or pdf.page_count<1 or pdf.is_repaired:raise RuntimeError('estrutura_pdf_invalida')
                for i in range(pdf.page_count):pdf.load_page(i)
        critical(events,'PyMuPDF.verificar_estrutura',verify)
        result['sucesso']=True
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        log(events,'erro_worker',tipo=type(exc).__name__)
    finally:
        result['arquivo_existe']=DEST.is_file();record()
        for el in reversed(held):
            try:critical(events,'releaseJavaObject',el.release_jabelement)
            except Exception:pass
        log(events,'worker_solicita_saida_normal')


def main():
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=logs/('concluir_fisico_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    result={'sucesso':False,'destino':str(DEST)};started=time.monotonic()
    props=Path.home()/'.accessibility.properties';before=props.read_bytes() if props.exists() else None
    try:
        critical(run/'supervisor.eventos.jsonl','preflight_dialogo_existente',identificar_dialogo)
        if DEST.exists():raise RuntimeError('destino_ja_existe')
        with (logs/'concluir_fisico_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        with (run/'stdout.txt').open('w') as out,(run/'stderr.txt').open('w') as err:
            p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',str(run)],stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            result['pid_worker']=p.pid
            try:p.wait(timeout=35)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=5);result['worker_timeout']=True
            result['worker_exit_code']=p.returncode
        if (run/'worker.resultado.json').exists():result.update(json.loads((run/'worker.resultado.json').read_text('utf-8')))
        if result.get('worker_timeout'):result['sucesso']=False
    except Exception as exc:result['erro_tipo']=type(exc).__name__
    finally:
        result.update(arquivo_existe=DEST.is_file(),total_segundos=round(time.monotonic()-started,4),
                      configuracao_preservada=before==(props.read_bytes() if props.exists() else None))
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]))
    else:main()
