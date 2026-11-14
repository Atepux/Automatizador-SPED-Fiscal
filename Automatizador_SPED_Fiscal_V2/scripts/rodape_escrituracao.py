"""Leitura do rodape Java; nenhum foco, clique ou dado fiscal nos logs."""
import re
import time
from datetime import datetime
from execucao_runtime import RESOURCES


def wait_main_ready(get_dialogs, main_ready, timeout=10, clock=time.monotonic, sleep=time.sleep):
    """Somente observa; qualquer modal persistente bloqueia a continuacao."""
    until = clock()+timeout
    while clock() < until:
        if not get_dialogs() and main_ready(): return
        sleep(.1)
    raise TimeoutError('interface_principal_nao_retornou_ou_modal_persistente')


def identity(text):
    cnpjs = [re.sub(r'\D', '', v) for v in re.findall(
        r'(?<!\d)(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})(?!\d)', text)]
    dates = []
    for value in re.findall(r'(?<!\d)\d{2}/\d{2}/\d{4}(?!\d)', text):
        try: dates.append(datetime.strptime(value, '%d/%m/%Y').date().isoformat())
        except ValueError: pass
    return cnpjs, dates


def compare(text, criteria):
    cnpjs, dates = identity(text)
    target = re.sub(r'\D', '', criteria['cnpj'])
    start = datetime.strptime(criteria['inicio'], '%d/%m/%Y').date().isoformat()
    end = datetime.strptime(criteria['fim'], '%d/%m/%Y').date().isoformat()
    return set(cnpjs) == {target} and dates == [start, end]


def read_footer(driver, criteria):
    """Descobre labels visiveis inferiores; devolve apenas metadados/booleanos.

    Candidatos devem conter CNPJ e duas datas, no mesmo label/text/status bar,
    abaixo da area central e fora de arvores, tabelas, menus ou visualizadores.
    Nenhuma coordenada e usada para interacao.
    """
    from pyjab.jabelement import JABElement
    root = driver.root_element
    area = root.bounds
    held = []; candidates = []; count = 0
    try:
        def walk(el, path=(), depth=0):
            nonlocal count
            count += 1
            if depth > 20 or count > 1000: raise RuntimeError('limite_rodape')
            role = el.role_en_us
            if role in {'table','tree','list','menu','menu bar','tool bar','viewport','password text'}:
                return
            if 'showing' not in el.states_en_us: return
            bounds = el.bounds
            lower = bounds['y'] >= area['y'] + area['height'] * .75
            if lower and role in {'label','text','status bar'}:
                values = [el.name]
                if el.accessible_text: values.append(el.text or '')
                for value in dict.fromkeys(values):
                    cnpjs, dates = identity(value)
                    if cnpjs or dates:
                        candidates.append({'indices':list(path),'papel':role,
                            'cnpj_presente':bool(cnpjs),'duas_datas':len(dates)==2,
                            'corresponde':compare(value, criteria)})
            if role == 'text': return
            for i in range(el.children_count):
                ctx = driver.bridge.getAccessibleChildFromContext(driver.vmid,el.accessible_context,i)
                if ctx:
                    child = JABElement(driver.bridge,driver.hwnd,driver.vmid,ctx)
                    held.append(child); walk(child,path+(i,),depth+1)
        walk(root)
        complete = [c for c in candidates if c['cnpj_presente'] and c['duas_datas']]
        # Diferentes controles concorrentes com identidade impedem aprovacao.
        paths = {tuple(c['indices']) for c in complete}
        ok = len(paths) == 1 and all(c['corresponde'] for c in complete)
        return {'rodape_lido':bool(complete),'identidade_corresponde':ok,
                'identidade_aberta_confirmada':ok,'geracao_liberada_por_identidade':ok,
                'candidatos':candidates}
    finally:
        for el in reversed(held): el.release_jabelement()


def main():
    import json, logging, subprocess, sys, tomllib
    from pathlib import Path
    from modal_concorrente import state
    from acessar_lista_escrituracoes import dialogs
    base = RESOURCES
    criteria = json.load(sys.stdin)
    if '--worker' not in sys.argv:
        run = base/'logs'/('rodape_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
        run.mkdir()
        timed_out = False
        with (run/'stdout.txt').open('w') as out, (run/'stderr.txt').open('w') as err:
            p = subprocess.Popen([sys.executable,'-u',__file__,'--worker',str(run)],
                stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW)
            try: p.communicate(json.dumps(criteria),timeout=20)
            except subprocess.TimeoutExpired:
                timed_out = True
                p.kill(); p.communicate(timeout=5)
                (run/'timeout.json').write_text('{"timeout":true}',encoding='utf-8')
        output = run/'resultado.json'
        result = json.loads(output.read_text('utf-8')) if output.exists() else {'rodape_lido':False,'timeout':True}
        if timed_out:
            result.update(timeout=True,identidade_aberta_confirmada=False,geracao_liberada_por_identidade=False)
            output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))
        return 0 if result.get('identidade_aberta_confirmada') else 1
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    logging.disable(logging.CRITICAL)
    def block(self): raise RuntimeError('alteracao_ambiente_bloqueada')
    Service.__wrapped__.enable_bridge = block
    d = None
    result = {'somente_leitura':True,'rodape_lido':False,'identidade_aberta_confirmada':False}
    try:
        hwnd,pid,_ = state()
        if dialogs(pid): raise RuntimeError('modal_aberta_nao_interagir')
        cfg = tomllib.loads((base/'config/diagnostico.toml').read_text('utf-8'))
        d = JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5)
        result.update(read_footer(d,criteria))
        if dialogs(pid):
            result.update(identidade_aberta_confirmada=False,geracao_liberada_por_identidade=False)
    except Exception as exc:
        result['erro_tipo'] = type(exc).__name__
        result.update(identidade_aberta_confirmada=False,geracao_liberada_por_identidade=False)
    finally:
        if d: d.detach()
        (Path(sys.argv[-1])/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    import sys
    sys.exit(main())
