"""Uma execucao coordenada: arvore -> clique fisico Salvar -> PDF unico."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import unicodedata
from modal_concorrente import ROOT,state,log,critical

DEST=ROOT/'saida/TESTE_FICTICIO/teste_integrado_operacoes_proprias.pdf'


def exigir_prontidao_ativacao(ar,require_subreports=False):
    if not ar.get('sucesso') or ar.get('erro_tipo'):raise RuntimeError('ativacao_falhou_proibir_exportacao')
    if require_subreports:
        checked=ar.get('subrelatorios') or {}
        if checked.get('final') is not True or checked.get('salvar_habilitado') is not True:
            raise RuntimeError('subrelatorios_nao_confirmados_proibir_exportacao')


def supervisor(run_override=None,case=None):
    global DEST
    import win32gui as g
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=run_override or logs/('ponta_a_ponta_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    if case is not None:
        DEST=Path(case['destino'])
        (run/'caso.json').write_text(json.dumps(case,ensure_ascii=False,indent=2),encoding='utf-8')
    events=run/'supervisor.jsonl'
    result={'sucesso':False,'destino':str(DEST),'workers':[]}
    props=Path.home()/'.accessibility.properties';before=props.read_bytes() if props.exists() else None
    started=time.monotonic();a=b=None;streams=[]
    def launch(mode):
        folder=run/mode;folder.mkdir()
        out=(folder/'stdout.txt').open('w');err=(folder/'stderr.txt').open('w');streams.extend([out,err])
        p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(folder)],
                           stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        log(events,'iniciar_worker',modo=mode,pid=p.pid)
        row={'modo':mode,'pid':p.pid};result['workers'].append(row)
        return p,row,time.monotonic()
    try:
        if DEST.exists():raise RuntimeError('destino_existe')
        main,pid,baseline=state()
        if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in baseline):raise RuntimeError('modal_inicial_aberta')
        with ((run/'autorizacao.lock') if case else logs/'ponta_a_ponta_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        result.update(pid_pva=pid,hwnd_principal=main)
        p,row,t=launch('relatorio')
        a=p
        try:p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            row['timeout_preservado']=True;raise
        row.update(exit_code=p.returncode,segundos=round(time.monotonic()-t,4))
        ar=json.loads((run/'relatorio/resultado.json').read_text('utf-8'))
        if case and case.get('id')=='recibo':
            result['janelas_recibo_observadas']=ar.get('janelas_recibo_observadas',[])
            if ar.get('pendencia_recibo')=='janela_adicional_requer_identificacao':
                result.update(status='pendente_identificacao_janela',pendencia_recibo=ar['pendencia_recibo'])
        if p.returncode!=0:raise RuntimeError('worker_relatorio_falhou')
        if case and case.get('opcional') and ar.get('erro_tipo')=='CaminhoAusente' and ar.get('cliques_tentados')==0:
            result.update(sucesso=True,ignorado=True,status='ignorado_indisponivel')
            return result
        exigir_prontidao_ativacao(ar,bool(case and case.get('exibir_subrelatorios')))
        if state()[:2]!=(main,pid):raise RuntimeError('pva_mudou_apos_relatorio')
        additional=state()[2]-baseline
        if additional and case and case.get('id')=='recibo':
            # Nao reinicia os cinco segundos: usa o prazo da ativacao.
            from janelas_recibo import identificar_janelas
            while additional:
                details=identificar_janelas(additional,pid)
                result['janelas_recibo']=details
                log(events,'identificar_janela_recibo_sem_acionar',janelas=details)
                if time.monotonic()>=ar.get('prazo_recibo_monotonic',0):
                    result['pendencia_recibo']='janela_identificada_exige_mapeamento_sem_confirmacao_automatica'
                    result['status']='pendente_identificacao_janela'
                    raise RuntimeError('recibo_pendente_janela_adicional')
                time.sleep(.1)
                if state()[:2]!=(main,pid):raise RuntimeError('pva_mudou')
                additional=state()[2]-baseline
        elif additional:raise RuntimeError('janela_inesperada_apos_relatorio')
        a,row,t=launch('abrir_salvar')
        deadline=time.monotonic()+25;save=None
        while time.monotonic()<deadline:
            current=state()
            if current[:2]!=(main,pid):raise RuntimeError('pva_mudou')
            new=current[2]-baseline
            expected={h for h in new if g.GetClassName(h)=='SunAwtDialog' and g.GetWindowText(h)=='Salvar'}
            if new-expected or len(expected)>1:raise RuntimeError('janela_inesperada')
            if len(expected)==1:save=next(iter(expected));break
            if a.poll() is not None:raise RuntimeError('abertura_salvar_falhou')
            time.sleep(.05)
        if save is None:raise TimeoutError('prazo_dialogo')
        result['hwnd_salvar']=save
        log(events,'dialogo_detectado',hwnd=save)
        b,brow,bt=launch('gravar')
        deadline=time.monotonic()+35
        while b.poll() is None and time.monotonic()<deadline:
            if state()[:2]!=(main,pid) or state()[2]-(baseline|{save}):raise RuntimeError('janela_inesperada_durante_gravacao')
            time.sleep(.05)
        if b.poll() is None:
            b.kill();b.wait(timeout=5);brow['timeout']=True
        brow.update(exit_code=b.returncode,segundos=round(time.monotonic()-bt,4))
        (run/'abrir_salvar/B_concluido.signal').write_text('worker de gravacao terminou',encoding='utf-8')
        try:a.wait(timeout=8)
        except subprocess.TimeoutExpired:row['timeout_saida_preservado']=True
        row.update(exit_code=a.poll(),segundos=round(time.monotonic()-t,4))
        wr=run/'gravar/worker.resultado.json'
        if wr.exists():result['pdf']=json.loads(wr.read_text('utf-8'))
        cr=run/'gravar/conteudo.resultado.json'
        if cr.exists():result['conteudo']=json.loads(cr.read_text('utf-8'))
        result['dialogo_fechado']=not g.IsWindowVisible(save)
        if state()[:2]!=(main,pid) or any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in state()[2]):raise RuntimeError('janela_inesperada_ao_final')
        result['sucesso']=bool(result.get('pdf',{}).get('sucesso') and b.returncode==0 and not brow.get('timeout') and a.returncode==0 and result['dialogo_fechado'])
        if case is not None and case.get('exigir_marcadores',True):
            result['sucesso']=result['sucesso'] and result.get('conteudo',{}).get('correspondencia')=='confirmada_por_marcadores'
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        log(events,'erro',tipo=type(exc).__name__)
    finally:
        if b is not None and b.poll() is None:
            b.kill();b.wait(timeout=5);result['B_encerrado_interrupcao']=True
        if a is not None:
            if (run/'abrir_salvar').exists():(run/'abrir_salvar/B_concluido.signal').write_text('B nao esta executando',encoding='utf-8')
            result['A_permanece_vivo']=a.poll() is None
        result.update(arquivo_existe=DEST.is_file(),total_segundos=round(time.monotonic()-started,4),
                      configuracao_preservada=before==(props.read_bytes() if props.exists() else None))
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        for f in streams:f.close()
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))
    return result


def worker(mode,folder):
    global DEST
    case_path=folder.parent/'caso.json'
    case=json.loads(case_path.read_text('utf-8')) if case_path.exists() else None
    if case:DEST=Path(case['destino'])
    if mode=='relatorio':
        if case:
            import ativar_operacoes_proprias as activation
            activation.TARGET=case['caminho_pva']
        from ativar_operacoes_proprias import worker as activate
        activate('click',folder/'resultado.json',lock_path=folder/'clique.lock',
                 require_subreports=bool(case and case.get('exibir_subrelatorios',False)),auto_expand=True,
                 receipt_wait=case.get('timeout_abertura_segundos',5) if case and case.get('id')=='recibo' else None)
    elif mode=='abrir_salvar':
        from testar_salvar_fisico import worker_a
        worker_a(folder,require_subreports=bool(case and case.get('exibir_subrelatorios',False)))
    elif mode=='gravar':
        import concluir_pdf_fisico as save
        save.DEST=DEST
        save.worker(folder)
        data=json.loads((folder/'worker.resultado.json').read_text('utf-8'))
        if not data.get('sucesso'):return
        import pymupdf
        def markers():
            groups=case['marcadores'] if case else {'operacoes_proprias':['operacoes proprias'],'apuracao_icms':['apuracao do icms']}
            found={name:False for name in groups}
            with pymupdf.open(DEST) as pdf:
                for page in pdf:
                    # Somente em memoria: nunca imprimir/gravar texto fiscal.
                    text=' '.join(''.join(c for c in unicodedata.normalize('NFKD',page.get_text().casefold()) if not unicodedata.combining(c)).split())
                    for name,alternatives in groups.items():
                        found[name] |= any(marker in text for marker in alternatives)
            return {'marcadores':found,'correspondencia':'confirmada_por_marcadores' if all(found.values()) else 'inconclusiva'}
        result=critical(folder/'worker.eventos.jsonl','conferir_marcadores_em_memoria',markers)
        (folder/'conteudo.resultado.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2],Path(sys.argv[3]))
    else:supervisor()
