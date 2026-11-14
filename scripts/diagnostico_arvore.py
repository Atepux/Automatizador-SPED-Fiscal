"""Leitura delimitada da aba Relatorios. Nao seleciona/expande nenhum no."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    import win32gui
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from pyjab.accessibleinfo import AccessibleActions
    from ctypes import byref
    logging.disable(logging.CRITICAL)
    cfg = tomllib.loads((ROOT / 'config/diagnostico.toml').read_text('utf-8'))
    result = {'data_utc': datetime.now(timezone.utc).isoformat(), 'somente_leitura': True,
              'estrutura': [], 'arvores': [], 'limites': {'profundidade': 22, 'nos': 700}}
    props = Path.home() / '.accessibility.properties'
    before = props.read_bytes() if props.exists() else None
    def block(self):
        raise RuntimeError('Alteracao bloqueada')
    Service.__wrapped__.enable_bridge = block
    driver, held = None, []
    try:
        windows = []
        win32gui.EnumWindows(lambda h, _: windows.append(h) if win32gui.IsWindowVisible(h) else None, None)
        roots = [h for h in windows if win32gui.GetWindowText(h).startswith(cfg['titulo_prefixo'])]
        if len(roots) != 1:
            raise RuntimeError('Janela principal ausente/ambigua')
        hwnd = roots[0]
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if any(win32process.GetWindowThreadProcessId(h)[1] == pid and
               win32gui.GetClassName(h) in {'SunAwtDialog', '#32770'} for h in windows):
            result['interrupcao'] = 'dialogo_aberto_nao_interagir'
            raise RuntimeError('Dialogo aberto')
        result.update(pid=pid, hwnd=hwnd)
        driver = JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5)
        result['conexao'] = True
        def visit(el, indices, depth, scope=False, tree=None, names=None):
            if len(result['estrutura']) >= 700 or depth > 22:
                result['inspecao_truncada'] = True
                return
            role, name = el.role_en_us, el.name.strip()
            # Isola exclusivamente os descendentes da aba de relatorios.
            scope = scope or (role == 'page tab' and name.lower() in {'relatórios', 'relatorios'})
            if scope and role == 'tree':
                tree = len(result['arvores'])
                result['arvores'].append({'indices': indices, 'selecao_acessivel': el.accessible_selection})
            in_tree = tree is not None
            safe_name = name if (scope and not re.search(r'\d[\d./ -]{7,}\d', name)) or name.lower() in {'relatórios', 'relatorios'} else '[omitido]' if name else ''
            path_names = (names or []) + ([safe_name] if in_tree and name else [])
            entry = {'indices': indices, 'papel': role, 'nome': safe_name,
                     'estados': el.states_en_us, 'filhos': el.children_count,
                     'escopo_relatorios': scope, 'arvore': tree}
            if in_tree:
                entry.update(caminho_nomes=path_names, selecao_acessivel=el.accessible_selection,
                             acao_acessivel=el.accessible_action)
                if el.accessible_action:
                    actions = AccessibleActions()
                    driver.bridge.getAccessibleActions(driver.vmid, el.accessible_context, byref(actions))
                    entry['acoes_disponiveis'] = [actions.actionInfo[i].name for i in range(min(actions.actionsCount, 32))]
            result['estrutura'].append(entry)
            if role in {'text', 'password text', 'table', 'list', 'menu bar', 'tool bar'} or (role == 'tree' and not scope):
                return
            for i in range(min(el.children_count, 700)):
                if len(result['estrutura']) >= 700:
                    result['inspecao_truncada'] = True
                    break
                context = driver.bridge.getAccessibleChildFromContext(driver.vmid, el.accessible_context, i)
                if context:
                    child = JABElement(driver.bridge, hwnd, driver.vmid, context)
                    held.append(child)
                    visit(child, indices + [i], depth + 1, scope, tree, path_names if in_tree else [])
        visit(driver.root_element, [], 0)
    except Exception as exc:
        result['erro_tipo'] = type(exc).__name__
    finally:
        for el in reversed(held):
            try:
                el.release_jabelement()
            except Exception:
                pass
        if driver:
            driver.detach()
        result['configuracao_preservada'] = before == (props.read_bytes() if props.exists() else None)
        folder = ROOT / 'logs'
        folder.mkdir(exist_ok=True)
        output = folder / ('arvore_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'log': str(output), 'arvores': result['arvores'],
                          'nos': len(result['estrutura']), 'erro': result.get('erro_tipo')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
