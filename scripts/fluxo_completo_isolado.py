"""Um relatorio, dois workers com timeout, nenhum retry de acao."""
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
DEST=ROOT/'saida/TESTE_FICTICIO/teste_fluxo_completo_operacoes.pdf'


def event(path,step,state,**extra):
    row={'timestamp':datetime.now(timezone.utc).isoformat(),'monotonic':time.monotonic(),
         'pid':os.getpid(),'chamada':step,'estado':state,**extra}
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,ensure_ascii=True)+'\n');f.flush();os.fsync(f.fileno())


def call(path,name,fn):
    start=time.monotonic();event(path,name,'antes')
    result=fn()
    event(path,name,'depois',segundos=round(time.monotonic()-start,4))
    return result


def windows():
    import win32gui as g
    import win32process
    all=[];g.EnumWindows(lambda h,_:all.append(h) if g.IsWindowVisible(h) else None,None)
    roots=[h for h in all if g.GetWindowText(h).startswith('Sped Fiscal - EFD ICMS/IPI')]
    if len(roots)!=1:raise RuntimeError('pva_ambiguo_ausente')
    _,pid=win32process.GetWindowThreadProcessId(roots[0])
    owned={h for h in all if win32process.GetWindowThreadProcessId(h)[1]==pid}
    return roots[0],pid,owned


def worker_b(run,hwnd,pid):
    import win32gui as g
    import win32process
    import pymupdf
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    log=run/'B.eventos.jsonl'
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    if DEST.exists():raise RuntimeError('destino_existe')
    main,current_pid,baseline=windows()
    if current_pid!=pid or hwnd not in baseline or g.GetWindowText(hwnd).casefold()!='salvar':
        raise RuntimeError('dialogo_nao_corresponde')
    cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
    # Aguarda o registro assincrono da janela no bridge; hwnd direto ignora
    # wait_java_window_by_title e pode verificar a janela cedo demais.
    d=call(log,'JABDriver.dialogo_aguardar_titulo',lambda:JABDriver(title='Salvar',bridge_dll=cfg['bridge_dll'],timeout=8))
    if d.hwnd!=hwnd:raise RuntimeError('bridge_conectou_janela_diferente')
    held=[];fields=[];buttons=[];count=0
    def walk(el,depth=0):
        nonlocal count
        count+=1
        if count>220 or depth>16:raise RuntimeError('limite_inspecao')
        role=el.role_en_us
        if role=='text' and el.name.strip().casefold()=='nome do arquivo:':fields.append(el)
        if role=='push button' and el.name.strip().casefold()=='salvar':buttons.append(el)
        if role in {'text','list','tree','table','password text'}:return
        for i in range(el.children_count):
            c=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
            if c:
                child=JABElement(d.bridge,hwnd,d.vmid,c);held.append(child);walk(child,depth+1)
    call(log,'inspecionar_dialogo',lambda:walk(d.root_element))
    if len(fields)!=1 or len(buttons)!=1:raise RuntimeError('controles_ambiguos')
    field,button=fields[0],buttons[0]
    if not {'enabled','editable','showing'}.issubset(field.states_en_us) or not {'enabled','showing'}.issubset(button.states_en_us):
        raise RuntimeError('controles_nao_habilitados')
    call(log,'field.send_text',lambda:field.send_text(str(DEST),simulate=False,wait_for_text_update=False))
    if not call(log,'field.text_readback',lambda:field.text==str(DEST)):raise RuntimeError('caminho_diverge')
    if windows()[2]-baseline:raise RuntimeError('janela_inesperada_antes_confirmacao')
    if DEST.exists():raise RuntimeError('destino_passou_existir')
    with (run/'confirmar_salvar.lock').open('x',encoding='utf-8') as f:f.write('uma tentativa')
    call(log,'botao_salvar._do_accessible_action',lambda:button._do_accessible_action('click'))
    def wait_file():
        previous=None;stable=0;deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            if windows()[2]-baseline:raise RuntimeError('janela_inesperada_apos_confirmacao')
            if DEST.is_file():
                s=DEST.stat();sig=(s.st_size,s.st_mtime_ns)
                stable=stable+1 if previous==sig and s.st_size>0 else 0;previous=sig
                if stable>=4 and not g.IsWindowVisible(hwnd):return
            time.sleep(.25)
        raise TimeoutError('gravacao_nao_concluida')
    call(log,'aguardar_arquivo_estavel',wait_file)
    def verify():
        with pymupdf.open(DEST) as pdf:
            if not pdf.is_pdf or pdf.needs_pass or pdf.page_count<1 or pdf.is_repaired:raise RuntimeError('pdf_invalido')
            for i in range(pdf.page_count):pdf.load_page(i)
            return {'sucesso':True,'pdf_abre':True,'paginas':pdf.page_count,'tamanho_bytes':DEST.stat().st_size,'reparado':pdf.is_repaired}
    result=call(log,'PyMuPDF.verificar_estrutura',verify)
    (run/'B.resultado.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # A bridge e liberada pelo encerramento do worker; nao usar __exit__ do driver.


def main():
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    resume=len(sys.argv)==3 and sys.argv[1]=='--continuar-sem-clique'
    resume_b=len(sys.argv)==3 and sys.argv[1]=='--continuar-conexao-B'
    if resume or resume_b:
        run=Path(sys.argv[2]).resolve()
        if run.parent!=logs.resolve():raise RuntimeError('pasta_invalida')
        prior=json.loads((run/'A.json').read_text('utf-8'))
        if resume:
            if prior.get('cliques_tentados')!=0 or (run/'ativacao.lock').exists():raise RuntimeError('nao_repetir_acao')
            (run/'A.preparacao_anterior.json').write_text(json.dumps(prior,ensure_ascii=False,indent=2),encoding='utf-8')
        else:
            rows=[json.loads(x) for x in (run/'B.eventos.jsonl').read_text('utf-8').splitlines()]
            if (run/'confirmar_salvar.lock').exists() or any(x['chamada'] not in {'JABDriver.dialogo','worker'} for x in rows):
                raise RuntimeError('B_ja_executou_acao_nao_repetir')
            (run/'B.conexao_anterior.jsonl').write_text((run/'B.eventos.jsonl').read_text('utf-8'),encoding='utf-8')
            (run/'resultado_anterior.json').write_text((run/'resultado.json').read_text('utf-8'),encoding='utf-8')
    else:
        run=logs/('completo_isolado_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    result={'destino':str(DEST),'sucesso':False,'workers':[]}
    props=Path.home()/'.accessibility.properties';before=props.read_bytes() if props.exists() else None
    started=time.monotonic()
    try:
        if DEST.exists():raise RuntimeError('destino_ja_existe')
        if not resume and not resume_b:
            with (logs/'completo_isolado_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        DEST.parent.mkdir(parents=True,exist_ok=True)
        main_hwnd,pid,baseline=windows()
        import win32gui as g
        if not resume_b and any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in baseline):raise RuntimeError('dialogo_inicial_inesperado')
        def launch(mode,extra=[]):
            start=time.monotonic()
            with (run/(mode+'.stdout.txt')).open('w') as out,(run/(mode+'.stderr.txt')).open('w') as err:
                p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(run),*extra],stdout=out,stderr=err)
                timeout=False
                try:p.wait(timeout=40)
                except subprocess.TimeoutExpired:
                    timeout=True;p.kill();p.wait(timeout=5)
            row={'modo':mode,'pid':p.pid,'exit_code':p.returncode,'timeout':timeout,'segundos':round(time.monotonic()-start,4)}
            result['workers'].append(row)
            return row
        if not resume_b:a=launch('A')
        if windows()[:2]!=(main_hwnd,pid):raise RuntimeError('pva_mudou')
        new=({h for h in baseline if g.GetClassName(h) in {'SunAwtDialog','#32770'}} if resume_b else windows()[2]-baseline)
        saves={h for h in new if g.GetClassName(h)=='SunAwtDialog' and g.GetWindowText(h).casefold()=='salvar'}
        if len(saves)!=1 or new-saves:raise RuntimeError('salvar_ausente_ou_janela_inesperada')
        # Timeout de A so permite B se a unica acao pendente foi a abertura modal,
        # e o dialogo esperado e confirmado externamente; nunca repetir o clique.
        ar=json.loads((run/'A.json').read_text('utf-8'))
        if not ar.get('sucesso') or ar.get('etapa') not in {'antes_abrir_salvar','depois_abrir_salvar'}:
            raise RuntimeError('ativacao_A_nao_confirmada')
        result['modal_hwnd']=next(iter(saves))
        b=launch('B',[str(result['modal_hwnd']),str(pid)])
        if b['timeout'] or b['exit_code']!=0:raise RuntimeError('worker_B_interrompido_sem_retry')
        result.update(json.loads((run/'B.resultado.json').read_text('utf-8')))
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
    finally:
        result.update(total_segundos=round(time.monotonic()-started,4),arquivo_existe=DEST.is_file(),
                      configuracao_preservada=before==(props.read_bytes() if props.exists() else None))
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        mode,run=sys.argv[2],Path(sys.argv[3])
        try:
            if mode=='A':
                from ativar_operacoes_proprias import worker
                worker('click',run/'A.json',open_dialog=True,lock_path=run/'ativacao.lock')
            else:worker_b(run,int(sys.argv[4]),int(sys.argv[5]))
        except Exception as exc:
            import traceback
            event(run/(mode+'.eventos.jsonl'),'worker','erro',tipo=type(exc).__name__,
                  pilha=[{'arquivo':Path(f.filename).name,'funcao':f.name,'linha':f.lineno} for f in traceback.extract_tb(exc.__traceback__)])
            sys.exit(1)
    else:main()
