"""Diagnostica JFileChooser; --preencher altera somente o campo identificado."""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = str(ROOT / 'saida' / 'TESTE_FICTICIO' / 'relatorio_teste.pdf')


def main():
    import win32gui
    import win32process
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    parser = argparse.ArgumentParser()
    parser.add_argument('--preencher', action='store_true')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    cfg = tomllib.loads((ROOT / 'config/diagnostico.toml').read_text('utf-8'))
    result = {'data_utc': datetime.now(timezone.utc).isoformat(), 'controles': [],
              'preenchimento_solicitado': args.preencher, 'salvamento_acionado': False}
    props = Path.home() / '.accessibility.properties'
    before = props.read_bytes() if props.exists() else None
    def no_write(self):
        raise RuntimeError('Alteracao de acessibilidade bloqueada')
    Service.__wrapped__.enable_bridge = no_write
    driver = None
    held = []
    stage = 'identificar_janela'
    try:
        windows = []
        win32gui.EnumWindows(lambda h, _: windows.append(h) if win32gui.IsWindowVisible(h) else None, None)
        roots = [h for h in windows if win32gui.GetWindowText(h).startswith(cfg['titulo_prefixo'])]
        if len(roots) != 1:
            raise RuntimeError('Janela principal ambigua/ausente')
        _, pid = win32process.GetWindowThreadProcessId(roots[0])
        dialogs = [h for h in windows if win32process.GetWindowThreadProcessId(h)[1] == pid
                   and win32gui.GetWindowText(h).strip().lower() in {'salvar', 'save', 'salvar como', 'save as'}]
        result['janelas_salvar_encontradas'] = len(dialogs)
        if len(dialogs) != 1:
            raise RuntimeError('Dialogo Salvar ambiguo/ausente')
        hwnd = dialogs[0]
        result.update(pid=pid, hwnd=hwnd, classe=win32gui.GetClassName(hwnd))
        stage = 'conectar'
        driver = JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5)
        result['conexao'] = True
        safe = {'salvar', 'cancelar', 'salvar em:', 'salvar em', 'nome do arquivo:',
                'nome do arquivo', 'arquivos do tipo:', 'arquivos do tipo', 'tipo de arquivo:',
                'save', 'cancel', 'file name:', 'file name', 'save in:', 'files of type:'}
        candidates = []
        stage = 'inspecionar'
        def visit(el, path, depth):
            if len(result['controles']) >= 180:
                return
            role, name = el.role_en_us, el.name
            clean = name.strip().lower()
            states = el.states_en_us
            result['controles'].append({'caminho_indices': path, 'funcao': role,
                'nome': name if clean in safe else '[omitido]' if name else '',
                'estados': states, 'filhos': el.children_count,
                'texto_acessivel': el.accessible_text})
            if role == 'text' and clean in {'nome do arquivo:', 'nome do arquivo', 'file name:', 'file name'}:
                candidates.append((el, path))
            if depth >= 12 or role in {'list', 'table', 'tree', 'text', 'password text'}:
                return
            for i in range(min(el.children_count, 180)):
                if len(result['controles']) >= 180:
                    break
                context = driver.bridge.getAccessibleChildFromContext(driver.vmid, el.accessible_context, i)
                if context:
                    child = JABElement(driver.bridge, hwnd, driver.vmid, context)
                    held.append(child)
                    visit(child, path + [i], depth + 1)
        visit(driver.root_element, [], 0)
        result['campos_nome_encontrados'] = len(candidates)
        if args.preencher:
            stage = 'preencher'
            if len(candidates) != 1:
                raise RuntimeError('Campo Nome do arquivo nao identificado univocamente')
            field, path = candidates[0]
            if not {'enabled', 'editable'}.issubset(set(field.states_en_us)):
                raise RuntimeError('Campo nao editavel/habilitado')
            if Path(TEST_PATH).exists():
                raise RuntimeError('Destino ficticio ja existe')
            # API Java Access Bridge via pyjab: sem foco, teclas, Enter ou acao de botao.
            driver.bridge.setTextContents(driver.vmid, field.accessible_context, TEST_PATH)
            driver._pump_messages()
            time.sleep(0.2)
            matches = field.text == TEST_PATH
            result.update(caminho_ficticio=TEST_PATH, campo_indices=path,
                          leitura_confirma_preenchimento=matches,
                          dialogo_permanece_aberto=bool(win32gui.IsWindowVisible(hwnd)),
                          arquivo_criado=Path(TEST_PATH).exists())
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
        result['configuracao_acessibilidade_preservada'] = before == (props.read_bytes() if props.exists() else None)
        folder = ROOT / 'logs'
        folder.mkdir(exist_ok=True)
        output = folder / ('campo_salvar_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'arquivo': str(output), **{k:v for k,v in result.items() if k != 'controles'}}, ensure_ascii=True))


if __name__ == '__main__':
    main()
