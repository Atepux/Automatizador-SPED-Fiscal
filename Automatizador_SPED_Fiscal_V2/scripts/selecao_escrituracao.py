"""Selecao unica autorizada. Criterios entram por stdin e nunca vao aos logs."""
from ctypes import byref
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import time
import tomllib

from diagnostico_escrituracoes import key, safe_header
from modal_concorrente import state, critical, log
from acessar_lista_escrituracoes import dialogs
from rodape_escrituracao import read_footer, wait_main_ready

from execucao_runtime import RESOURCES,focus_window
ROOT = RESOURCES


def digits(value):
    return re.sub(r'\D', '', value)


def date(value):
    value = value.strip()
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError('data_nao_reconhecida')


def validate(criteria):
    if len(digits(criteria['cnpj'])) != 14:
        raise ValueError('cnpj_invalido')
    if date(criteria['inicio']) > date(criteria['fim']):
        raise ValueError('periodo_invalido')


def matches(row, criteria):
    return (digits(row['CPF/CNPJ']) == digits(criteria['cnpj'])
            and date(row['Data Inicial']) == date(criteria['inicio'])
            and date(row['Data Final']) == date(criteria['fim']))


def unique(rows, criteria):
    """Nunca seleciona a primeira de varias; filtros extras tambem sao exigidos."""
    found = [(i, row) for i, row in rows if matches(row, criteria)]
    for field, target in [('Inscrição Estadual', criteria.get('ie')),
                          ('Finalidade do Arquivo', criteria.get('finalidade')),
                          ('Estado', criteria.get('estado'))]:
        if target:
            def norm(value):
                return digits(value) if field == 'Inscrição Estadual' else key(value)
            found = [(i, row) for i, row in found if norm(row[field]) == norm(target)]
    if len(found) != 1:
        raise RuntimeError('correspondencia_ausente_ou_ambigua')
    return found[0][0]


def worker(criteria, run, mode):
    import win32gui as g
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from pyjab.accessibleinfo import AccessibleTableInfo, AccessibleTableCellInfo
    logging.disable(logging.CRITICAL)
    result = {'modo': mode, 'correspondencia_unica': False, 'selecao_confirmada': False,
              'ok_tentativas': 0, 'identidade_aberta_confirmada': False}
    events = run/'eventos.jsonl'
    held = []; driver = None
    def block(self):
        raise RuntimeError('alteracao_ambiente_bloqueada')
    Service.__wrapped__.enable_bridge = block
    def save():
        (run/'resultado.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    def connect(hwnd):
        return critical(events, 'conectar_java', lambda: JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5))
    def walk(el, path=(), depth=0):
        if depth > 20 or len(held) > 1600:
            raise RuntimeError('limite_inspecao')
        yield el, path
        if el.role_en_us in {'table','list','tree','text','password text'}:
            return
        for i in range(el.children_count):
            ctx = driver.bridge.getAccessibleChildFromContext(driver.vmid, el.accessible_context, i)
            if ctx:
                child = JABElement(driver.bridge, driver.hwnd, driver.vmid, ctx)
                held.append(child)
                yield from walk(child, path+(i,), depth+1)
    def release():
        nonlocal driver
        for el in reversed(held):
            try: el.release_jabelement()
            except Exception: pass
        held.clear()
        if driver:
            driver.detach(); driver = None
    try:
        cfg = tomllib.loads((ROOT/'config/diagnostico.toml').read_text('utf-8'))
        validate(criteria)
        main, pid, _ = state()
        current = dialogs(pid)
        if len(current) != 1 or current[0]['titulo'] != 'Abrir Escrituração' or current[0]['classe'] != 'SunAwtDialog':
            raise RuntimeError('dialogo_esperado_ausente_ou_ambiguo')
        hwnd = current[0]['hwnd']; driver = connect(hwnd)
        controls = list(walk(driver.root_element))
        tables = [e for e, _ in controls if e.role_en_us == 'table']
        if len(tables) != 1:
            raise RuntimeError('tabela_ausente_ou_ambigua')
        table = tables[0]
        info = table._get_accessible_table_info()
        header = AccessibleTableInfo(); columns = {}
        if not driver.bridge.getAccessibleTableColumnHeader(driver.vmid, table.accessible_context, byref(header)):
            raise RuntimeError('cabecalho_indisponivel')
        try:
            for col in range(header.columnCount):
                cell = AccessibleTableCellInfo()
                if not driver.bridge.getAccessibleTableCellInfo(driver.vmid, header.accessibleTable, 0, col, byref(cell)):
                    raise RuntimeError('cabecalho_ilegivel')
                el = JABElement(driver.bridge, hwnd, driver.vmid, cell.accessibleContext)
                try: name = safe_header(el.name)
                finally: el.release_jabelement()
                if name in columns: raise RuntimeError('cabecalho_duplicado')
                columns[name] = col
        finally:
            for field in ('caption','summary','accessibleContext','accessibleTable'):
                ref = getattr(header, field)
                if ref: driver.bridge.releaseJavaObject(driver.vmid, ref)
        required = ['CPF/CNPJ','Data Inicial','Data Final','Inscrição Estadual','Finalidade do Arquivo','Estado']
        if not all(name in columns for name in required):
            raise RuntimeError('coluna_obrigatoria_ausente')
        result['colunas_mapeadas'] = required
        def read(row, name):
            el = table.get_cell(row, columns[name])
            try: return el.name or el.text or ''
            finally: el.release_jabelement()
        def record(row):
            return {name: read(row, name) for name in required}
        rows = []
        for row in range(info.rowCount):
            if digits(read(row, 'CPF/CNPJ')) == digits(criteria['cnpj']):
                rows.append((row, record(row)))
        index = unique(rows, criteria)
        result['correspondencia_unica'] = True
        result['criterio_estado_conferido'] = bool(criteria.get('estado'))
        save()
        if mode == 'inspecionar': return
        if dialogs(pid) != current: raise RuntimeError('janela_alterada')
        if unique([(index, record(index))], criteria) != index:
            raise RuntimeError('registro_alterado')
        if table.selected_rows != [index]:
            critical(events, 'selecionar_linha_java', lambda: table.select_row(index))
        else:
            log(events, 'linha_correta_ja_selecionada_sem_nova_selecao')
        driver._pump_messages()
        if table.selected_rows != [index] or not table.is_row_selected(index):
            raise RuntimeError('selecao_nao_confirmada')
        unique([(index, record(index))], criteria)
        result['selecao_confirmada'] = True; save()
        buttons = [e for e, _ in controls if e.role_en_us == 'push button' and e.name == 'Ok']
        if len(buttons) != 1 or not {'enabled','showing'}.issubset(buttons[0].states_en_us):
            raise RuntimeError('ok_indisponivel')
        # Sem teclas sinteticas nem driver.focus(), que pode enviar espaco.
        critical(events,'ativar_dialogo_sem_teclas',lambda:focus_window(hwnd))
        if g.GetForegroundWindow() != hwnd or dialogs(pid) != current:
            raise RuntimeError('foco_ou_dialogo_alterado')
        result['ok_tentativas'] = 1; save()
        critical(events, 'ok_clique_fisico_dinamico', lambda: buttons[0].click(simulate=True))
        # Uma janela transitoria nao e erro por si so. Nao interagir com ela;
        # aguardar todas as modais desaparecerem e a principal ficar habilitada.
        opening_deadline = time.monotonic()+30
        wait_main_ready(lambda: dialogs(pid),
                        lambda: (not g.IsWindowVisible(hwnd) and g.IsWindowVisible(main)
                                 and g.IsWindowEnabled(main)), timeout=30)
        result['dialogo_fechado'] = True; save(); release()
        # O dialogo de carregamento pode aparecer DEPOIS de a selecao sumir.
        # Nao repetir Ok; aguardar e reler somente a identidade, dentro do prazo.
        while time.monotonic() < opening_deadline:
            wait_main_ready(lambda: dialogs(pid),
                lambda: g.IsWindowVisible(main) and g.IsWindowEnabled(main),
                timeout=max(.1,opening_deadline-time.monotonic()))
            driver = connect(main)
            footer = critical(events,'ler_e_conferir_rodape',lambda:read_footer(driver,criteria))
            if not dialogs(pid) and footer['rodape_lido']:
                result.update(footer)
                if not footer['identidade_aberta_confirmada']:
                    raise RuntimeError('identidade_ativa_nao_confirmada_nao_prosseguir')
                break
            release()
            time.sleep(.1)
        else:
            raise TimeoutError('carregamento_ou_rodape_nao_confirmado_em_30s')
    except Exception as exc:
        result.update(identidade_aberta_confirmada=False,geracao_liberada_por_identidade=False)
        result['erro_tipo'] = type(exc).__name__
        # Somente mensagens internas conhecidas, nunca excecoes de bibliotecas.
        if str(exc) in {'correspondencia_ausente_ou_ambigua','selecao_nao_confirmada','identidade_ativa_nao_confirmada_nao_prosseguir','foco_nao_confirmado'}:
            result['motivo'] = str(exc)
        import traceback
        log(events, 'falha', tipo=type(exc).__name__, pilha=[{'funcao':f.name,'linha':f.lineno} for f in traceback.extract_tb(exc.__traceback__)])
    finally:
        save(); release()


def main():
    mode = 'selecionar' if '--selecionar' in sys.argv else 'inspecionar'
    criteria = json.load(sys.stdin); validate(criteria)
    if '--worker' in sys.argv:
        worker(criteria, Path(sys.argv[-1]), mode); return
    run = ROOT/'logs'/('selecao_unica_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    run.mkdir(parents=True)
    timed_out = False
    with (run/'worker.stdout').open('w') as out, (run/'worker.stderr').open('w') as err:
        process = subprocess.Popen([sys.executable,'-u',__file__,'--worker','--'+mode,str(run)],
                                   stdin=subprocess.PIPE, stdout=out, stderr=err,
                                   creationflags=subprocess.CREATE_NO_WINDOW, text=True, encoding='utf-8')
        try: process.communicate(json.dumps(criteria), timeout=55)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill(); process.communicate(timeout=5)
            (run/'timeout.json').write_text('{"timeout":true,"somente_worker_encerrado":true}', encoding='utf-8')
    result = json.loads((run/'resultado.json').read_text('utf-8')) if (run/'resultado.json').exists() else {'inconclusivo':True}
    if timed_out:
        result.update(timeout=True,identidade_aberta_confirmada=False,geracao_liberada_por_identidade=False)
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pasta_log':str(run),'resultado':result}, ensure_ascii=True))
    return 0 if (result.get('identidade_aberta_confirmada') if mode == 'selecionar' else result.get('correspondencia_unica')) and not result.get('erro_tipo') else 1


if __name__ == '__main__': sys.exit(main())
