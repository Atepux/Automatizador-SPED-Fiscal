"""Teste unico autorizado de AccessibleSelection; sem clique/teclas/fallback."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PATH = ['Escrituração Fiscal', 'Relatórios de Registros Fiscais',
        'Apuração do ICMS', 'Operações Próprias']


def main():
    import win32gui
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    cfg = tomllib.loads((ROOT / 'config/diagnostico.toml').read_text('utf-8'))
    folder = ROOT / 'logs'
    folder.mkdir(exist_ok=True)
    output = folder / ('selecao_operacoes_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    result = {'data_utc': datetime.now(timezone.utc).isoformat(), 'caminho': PATH,
              'tentativas_selecao': 0, 'sucesso_completo': False}
    props = Path.home() / '.accessibility.properties'
    before = props.read_bytes() if props.exists() else None
    def block(self):
        raise RuntimeError('alteracao_config_bloqueada')
    Service.__wrapped__.enable_bridge = block
    driver, held = None, []
    stage = 'identificacao'
    def stop(reason):
        result['interrupcao'] = reason
        raise RuntimeError(reason)
    def record():
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        def windows():
            found = []
            win32gui.EnumWindows(lambda h, _: found.append(h) if win32gui.IsWindowVisible(h) else None, None)
            return found
        roots = [h for h in windows() if win32gui.GetWindowText(h).startswith(cfg['titulo_prefixo'])]
        if len(roots) != 1:
            stop('janela_pva_ambigua_ou_ausente')
        hwnd = roots[0]
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        def owned():
            return {h for h in windows() if win32process.GetWindowThreadProcessId(h)[1] == pid}
        baseline = owned()
        if any(win32gui.GetClassName(h) in {'SunAwtDialog', '#32770'} for h in baseline):
            stop('dialogo_aberto')
        driver = JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5)
        result.update(pid=pid, hwnd=hwnd)
        def children(el):
            if el.children_count > 700:
                stop('limite_filhos')
            found = []
            for i in range(el.children_count):
                context = driver.bridge.getAccessibleChildFromContext(driver.vmid, el.accessible_context, i)
                if context:
                    child = JABElement(driver.bridge, hwnd, driver.vmid, context)
                    held.append(child)
                    found.append((i, child))
            return found
        count = 0
        def scan(el, scoped=False, depth=0):
            nonlocal count
            count += 1
            if depth > 24 or count > 900:
                stop('limite_varredura')
            role = el.role_en_us
            scoped = scoped or (role == 'page tab' and el.name == 'Relatórios')
            if role == 'tree':
                return [el] if scoped else []
            if role in {'menu bar', 'tool bar', 'text', 'list', 'table', 'password text'}:
                return []
            found = []
            for _, child in children(el):
                found.extend(scan(child, scoped, depth+1))
            return found
        stage = 'resolver_caminho'
        trees = scan(driver.root_element)
        if len(trees) != 1:
            stop('arvore_nao_univoca')
        parent = trees[0]
        checks = []
        for pos, name in enumerate(PATH):
            matches = [(i,c) for i,c in children(parent) if c.name == name]
            if len(matches) != 1:
                stop('segmento_ausente_ou_ambiguo')
            index, node = matches[0]
            states = node.states_en_us
            checks.append({'nome': name, 'indice_local': index, 'estados': states})
            if not {'visible', 'showing'}.issubset(states):
                stop('no_nao_visivel')
            if pos < len(PATH)-1:
                if 'expanded' not in states:
                    stop('pai_nao_expandido')
                parent = node
        result['verificacao_caminho'] = checks
        result['pai_permite_selecao'] = parent.accessible_selection
        if not parent.accessible_selection:
            stop('pai_sem_interface_selecao')
        result['selecionado_antes'] = 'selected' in node.states_en_us
        if result['selecionado_antes']:
            stop('alvo_ja_selecionado_teste_nao_comprova_mudanca')
        # Registra somente coincidencias com titulos conhecidos, nunca nomes livres.
        def viewer_matches():
            found, visited = [], 0
            def walk(el, depth=0, in_tree=False):
                nonlocal visited
                visited += 1
                if visited > 900 or depth > 24:
                    return
                role = el.role_en_us
                if role in {'tree','menu bar','tool bar','table','list','password text'}:
                    return
                if {'showing','visible'}.issubset(el.states_en_us):
                    name = el.name.casefold()
                    if role in {'label', 'panel', 'page tab', 'internal frame'} and 'operações próprias' in name:
                        found.append({'papel': role, 'titulo_reconhecido': 'Operações Próprias'})
                if role == 'text':
                    return
                for _, child in children(el):
                    walk(child, depth+1)
            walk(driver.root_element)
            return found
        result['evidencias_visualizador_antes'] = viewer_matches()
        if owned() - baseline:
            stop('janela_inesperada_antes')
        stage = 'selecao_unica'
        with (folder / 'selecao_operacoes_acionada.lock').open('x', encoding='utf-8') as lock:
            lock.write(str(output))
        result['tentativas_selecao'] = 1
        record()
        driver.bridge.addAccessibleSelectionFromContext(driver.vmid, parent.accessible_context, index)
        result['chamada_retornou'] = True
        stage = 'confirmacao'
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            driver._pump_messages()
            if owned() - baseline:
                stop('janela_inesperada_apos_selecao')
            result['no_selecionado_apos'] = 'selected' in node.states_en_us
            result['evidencias_visualizador_apos'] = viewer_matches()
            if result['no_selecionado_apos'] and result['evidencias_visualizador_apos']:
                result['sucesso_completo'] = True
                break
            time.sleep(0.5)
    except Exception as exc:
        result.update(erro_tipo=type(exc).__name__, erro_etapa=stage)
    finally:
        for el in reversed(held):
            try:
                el.release_jabelement()
            except Exception:
                pass
        if driver:
            driver.detach()
        result['configuracao_preservada'] = before == (props.read_bytes() if props.exists() else None)
        record()
        print(json.dumps({'log': str(output), **result}, ensure_ascii=True))


if __name__ == '__main__':
    main()
