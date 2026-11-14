"""Ativacao de Operacoes Proprias e inspecao sem salvar PDF."""
from datetime import datetime
from ctypes import byref
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from modal_concorrente import ROOT,state,critical,log


def inspect_worker(run):
    import win32gui as g
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from pyjab.accessibleinfo import AccessibleActions
    logging.disable(logging.CRITICAL)
    def block(self):raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge=block
    events=run/'inspecao.eventos.jsonl';result={'sucesso':False,'opcoes':[]};held=[];d=None
    try:
        hwnd,pid,owned=state()
        if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in owned):raise RuntimeError('modal_aberta')
        cfg=tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        d=critical(events,'JABDriver.principal',lambda:JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5))
        count=0
        def walk(el,path,depth=0):
            nonlocal count
            count+=1
            if count>900 or depth>24:raise RuntimeError('limite_inspecao')
            role=el.role_en_us
            if role=='check box':
                name=el.name;description=el.description
                match='subrelat' in name.casefold() or 'subrelat' in description.casefold()
                if match:
                    actions=AccessibleActions()
                    if el.accessible_action:d.bridge.getAccessibleActions(d.vmid,el.accessible_context,byref(actions))
                    result['opcoes'].append({'nome':name if 'subrelat' in name.casefold() else '[omitido]',
                        'descricao':description if 'subrelat' in description.casefold() else '',
                        'funcao':role,'estados':el.states_en_us,'checked':el.is_checked(),
                        'indices':path,'bounds':el.bounds,
                        'acoes':[actions.actionInfo[i].name for i in range(min(actions.actionsCount,32))]})
            if role in {'tree','text','list','table','password text','menu bar'}:return
            for i in range(min(el.children_count,700)):
                context=d.bridge.getAccessibleChildFromContext(d.vmid,el.accessible_context,i)
                if context:
                    c=JABElement(d.bridge,hwnd,d.vmid,context);held.append(c);walk(c,path+[i],depth+1)
        critical(events,'inspecionar_checkbox',lambda:walk(d.root_element,[]))
        result['sucesso']=len(result['opcoes'])==1
    except Exception as exc:result['erro_tipo']=type(exc).__name__
    finally:
        (run/'inspecao.resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        for el in reversed(held):
            try:el.release_jabelement()
            except Exception:pass
        if d:d.detach()


def main():
    run=ROOT/'logs'/('subrelatorios_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir(parents=True)
    result={'sucesso':False,'salvamento_executado':False};started=time.monotonic()
    try:
        with (ROOT/'logs/subrelatorios_diagnostico.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        for mode in ['ativar','inspecionar']:
            with (run/(mode+'.stdout')).open('w') as out,(run/(mode+'.stderr')).open('w') as err:
                p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',mode,str(run)],stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
                try:p.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    result.update(timeout=mode,pid_preservado=p.pid);break
                if p.returncode!=0:raise RuntimeError('worker_falhou')
            if mode=='ativar':
                if not json.loads((run/'ativacao.json').read_text('utf-8')).get('sucesso'):raise RuntimeError('ativacao_nao_confirmada')
            else:result.update(json.loads((run/'inspecao.resultado.json').read_text('utf-8')))
    except Exception as exc:result['erro_tipo']=type(exc).__name__
    finally:
        result['segundos']=round(time.monotonic()-started,4)
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        mode,run=sys.argv[2],Path(sys.argv[3])
        if mode=='ativar':
            from ativar_operacoes_proprias import worker
            worker('click',run/'ativacao.json',lock_path=run/'ativacao.lock')
        else:inspect_worker(run)
    else:main()
