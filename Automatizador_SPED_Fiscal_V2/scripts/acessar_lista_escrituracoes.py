"""Somente Fechar atual e Abrir lista; nunca confirma abertura de registro."""
from datetime import datetime
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from diagnostico_escrituracoes import safe_name
from modal_concorrente import state,critical,log

from execucao_runtime import RESOURCES,focus_window
ROOT=RESOURCES


def dialogs(pid):
    import win32gui as g
    import win32process
    found=[]
    def see(h,_):
        if g.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1]==pid and g.GetClassName(h) in {'SunAwtDialog','#32770'}:
            found.append({'hwnd':h,'classe':g.GetClassName(h),'titulo':safe_name(g.GetWindowText(h))})
    g.EnumWindows(see,None)
    return found


def command_worker(mode,run):
    import win32gui as g
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    events=run/(mode+'.jsonl');result={'modo':mode,'sucesso':False,'comando_tentativas':0}
    held=[];d=None
    def record():
        (run/(mode+'.resultado.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    try:
        hwnd,pid,_=state();result.update(pid_pva=pid,hwnd=hwnd)
        if dialogs(pid):raise RuntimeError('dialogo_preexistente_nao_confirmar')
        title=g.GetWindowText(hwnd)
        if '*' in title:raise RuntimeError('indicador_possivel_alteracao_pendente')
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        d=JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5)
        def children(el):
            if el.children_count>300:raise RuntimeError('limite_filhos')
            out=[]
            for i in range(el.children_count):
                ctx=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
                if ctx:
                    c=JABElement(d.bridge,hwnd,d.vmid,ctx);held.append(c);out.append(c)
            return out
        def menu():
            from backend_empresa import locate_menu
            return locate_menu(d.root_element,children)
        target='Fechar' if mode=='fechar' else 'Abrir'
        m=menu();items=[c for c in children(m) if c.role_en_us=='menu item' and c.name==target]
        if len(items)!=1:raise RuntimeError('comando_ambiguo')
        item=items[0]
        if mode=='fechar' and 'enabled' not in item.states_en_us:
            result.update(sucesso=True,fechamento_dispensado=True);return
        if 'enabled' not in item.states_en_us:raise RuntimeError('comando_desabilitado')
        critical(events,'ativar_janela_pva_sem_teclas',lambda:focus_window(hwnd))
        critical(events,'abrir_menu_escrituracao',lambda:m.click(simulate=True))
        d._pump_messages()
        # Nova referencia do item apos abrir o menu.
        m=menu();items=[c for c in children(m) if c.role_en_us=='menu item' and c.name==target]
        if len(items)!=1 or not {'enabled','showing'}.issubset(items[0].states_en_us):raise RuntimeError('comando_nao_visivel')
        if dialogs(pid):raise RuntimeError('aviso_inesperado_antes_comando')
        result['comando_tentativas']=1;record()
        critical(events,'menu_'+target+'_clique_dinamico',lambda:items[0].click(simulate=True))
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            d._pump_messages()
            current=dialogs(pid)
            if current:
                result['dialogos']=current
                if mode=='fechar':raise RuntimeError('aviso_ao_fechar_nao_confirmar')
                result['sucesso']=True
                record()
                while not (run/'inspecao_concluida.signal').exists():
                    d._pump_messages();time.sleep(.05)
                return
            if mode=='fechar':
                fresh=menu();opens=[c for c in children(fresh) if c.role_en_us=='menu item' and c.name=='Abrir']
                if len(opens)==1 and 'enabled' in opens[0].states_en_us:
                    result.update(sucesso=True,abrir_habilitado_apos_fechar=True);return
            time.sleep(.1)
        raise TimeoutError('prazo_sem_resultado_do_comando')
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        if str(exc) in {'foco_nao_confirmado','dialogo_preexistente_nao_confirmar','indicador_possivel_alteracao_pendente','comando_desabilitado','comando_nao_visivel','aviso_ao_fechar_nao_confirmar','comando_ambiguo','aviso_inesperado_antes_comando'}:
            result['motivo']=str(exc)
        # Somente mensagens internas controladas; nao registrar texto do PVA.
        import traceback
        log(events,'erro',tipo=type(exc).__name__,pilha=[{'funcao':f.name,'linha':f.lineno,'arquivo':Path(f.filename).name} for f in traceback.extract_tb(exc.__traceback__)])
    finally:
        record()
        for el in reversed(held):
            try:el.release_jabelement()
            except Exception:pass
        if d:d.detach()


def main():
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=logs/('lista_escrituracoes_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    result={'escrituracao_aberta_automaticamente':False,'relatorios_executados':False}
    handles=[];opener=None;inspector=None
    def launch(mode):
        out=(run/(mode+'.stdout')).open('w');err=(run/(mode+'.stderr')).open('w');handles.extend([out,err])
        if mode=='inspecionar':cmd=[sys.executable,'-u',str(ROOT/'scripts/diagnostico_escrituracoes.py'),str(run/'interface.json')]
        else:cmd=[sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(run)]
        return subprocess.Popen(cmd,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        with (logs/'acessar_lista_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        p=launch('fechar')
        try:p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            result.update(worker_preservado=p.pid,timeout='fechar');raise
        closed=json.loads((run/'fechar.resultado.json').read_text('utf-8'));result['fechar']=closed
        if not closed['sucesso']:raise RuntimeError('fechamento_nao_confirmado')
        opener=launch('abrir');deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            _,pid,_=state();current=dialogs(pid)
            if current:
                if len(current)!=1 or current[0]['titulo']=='[omitido]':
                    result['dialogo_nao_identificado']=current;raise RuntimeError('nao_inspecionar_dialogo_desconhecido')
                result['janela_lista']=current[0];break
            if opener.poll() is not None:raise RuntimeError('abrir_nao_apresentou_lista')
            time.sleep(.05)
        else:raise TimeoutError('abrir_sem_dialogo')
        inspector=launch('inspecionar')
        try:inspector.wait(timeout=25)
        except subprocess.TimeoutExpired:inspector.kill();inspector.wait(timeout=5);raise
        result['inspecao_exit_code']=inspector.returncode
        (run/'inspecao_concluida.signal').write_text('terminou',encoding='utf-8')
        try:opener.wait(timeout=8)
        except subprocess.TimeoutExpired:result['abridor_preservado']=opener.pid
    except Exception as exc:result['erro_tipo']=type(exc).__name__
    finally:
        if inspector is not None and inspector.poll() is None:inspector.kill();inspector.wait(timeout=5)
        (run/'inspecao_concluida.signal').write_text('sem inspecao pendente',encoding='utf-8')
        if opener is not None:result['abridor_ainda_vivo']=opener.poll() is None
        (run/'resumo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        for f in handles:f.close()
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':command_worker(sys.argv[2],Path(sys.argv[3]))
    else:main()
