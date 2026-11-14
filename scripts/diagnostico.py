"""Inspecao somente de leitura. Nao inicia, ativa ou encerra o PVA."""
import ctypes
import importlib.metadata
import json
import logging
from pathlib import Path
import struct
import sys
import tomllib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    import win32gui
    import win32process
    import win32api
    cfg = tomllib.loads((ROOT / 'config/diagnostico.toml').read_text('utf-8'))
    result = {'data_utc': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'python_bits': struct.calcsize('P') * 8,
              'pyjab': importlib.metadata.version('pyjab'), 'controles': [],
              'privacidade': 'Sem textos de documentos, descricoes, celulas ou nomes dinamicos.'}
    props = Path.home() / '.accessibility.properties'
    before = props.read_bytes() if props.exists() else None
    driver = None
    logging.disable(logging.CRITICAL)
    try:
        windows = []
        def enum(hwnd, _):
            title = win32gui.GetWindowText(hwnd)
            if win32gui.IsWindowVisible(hwnd) and title.startswith(cfg['titulo_prefixo']):
                windows.append(hwnd)
        win32gui.EnumWindows(enum, None)
        if len(windows) != 1:
            raise RuntimeError(f'Esperada uma janela PVA; encontradas {len(windows)}.')
        hwnd = windows[0]
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(0x1000, False, pid)
        try:
            size = ctypes.c_ulong(32768)
            buf = ctypes.create_unicode_buffer(size.value)
            query = ctypes.windll.kernel32.QueryFullProcessImageNameW
            query.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
            if not query(int(handle), 0, buf, ctypes.byref(size)):
                raise ctypes.WinError()
            image = Path(buf.value)
        finally:
            handle.Close()
        with image.open('rb') as f:
            f.seek(0x3c)
            offset = struct.unpack('<I', f.read(4))[0]
            f.seek(offset + 4)
            machine = struct.unpack('<H', f.read(2))[0]
        runtime = image.parent.parent
        release = {}
        for line in (runtime / 'release').read_text('utf-8').splitlines():
            key, _, val = line.partition('=')
            if key in {'JAVA_VERSION', 'JAVA_RUNTIME_VERSION', 'OS_ARCH', 'IMPLEMENTOR'}:
                release[key] = val.strip('"')
        result.update(pid=pid, hwnd=hwnd, classe_janela=win32gui.GetClassName(hwnd),
                      executavel=str(image), processo_bits={0x8664:64, 0x14c:32}.get(machine),
                      runtime=release, bridge_dll=cfg['bridge_dll'])
        from pyjab.common.service import Service
        # Modifica apenas a classe em memoria, nunca o pacote ou o ambiente.
        def block_write(self):
            raise RuntimeError('pyjab tentou habilitar/regravar acessibilidade; operacao bloqueada.')
        Service.__wrapped__.enable_bridge = block_write
        from pyjab.jabdriver import JABDriver
        driver = JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5)
        result['conexao'] = 'sucesso'
        result['versoes_bridge'] = driver.get_version_info()
        # Apenas nomes estaticos conhecidos; qualquer outro nome fica omitido.
        safe = {'Arquivo', 'Escrituracao', 'Escrituração', 'Relatórios', 'Relatorios',
                'Ajuda', 'Configurações', 'Ferramentas', 'Sair', 'Importar', 'Abrir',
                'Fechar', 'Editar', 'Visualizar', 'Pesquisar', 'Novo', 'Excluir',
                'Validar', 'Transmitir', 'Gerar', 'Imprimir', 'Cancelar', 'OK'}
        blocked = {'table', 'list', 'tree', 'text', 'password text'}
        def visit(element, path, depth):
            if len(result['controles']) >= cfg['max_controles']:
                result['limite_controles'] = True
                return
            role = element.role_en_us
            name = element.name
            result['controles'].append({'caminho_indices': path,
                'nome': name if name in safe else '[omitido]' if name else '',
                'funcao': role, 'estados': element.states_en_us,
                'indice_no_pai': element.index_in_parent,
                'quantidade_filhos': element.children_count})
            if depth >= cfg['max_profundidade'] or role in blocked:
                return
            for index in range(min(element.children_count, cfg['max_controles'])):
                if len(result['controles']) >= cfg['max_controles']:
                    break
                context = driver.bridge.getAccessibleChildFromContext(driver.vmid, element.accessible_context, index)
                if not context:
                    continue
                from pyjab.jabelement import JABElement
                child = JABElement(bridge=driver.bridge, hwnd=hwnd, vmid=driver.vmid, accessible_context=context)
                try:
                    visit(child, path + [index], depth + 1)
                finally:
                    child.release_jabelement()
        visit(driver.root_element, [], 0)
    except Exception as exc:
        result['conexao'] = result.get('conexao', 'falha')
        # Excecoes da biblioteca podem conter textos de controles: nao gravar str(exc).
        result['erro_tipo'] = type(exc).__name__
        result['erro_etapa'] = 'inspecao' if result['conexao'] == 'sucesso' else 'identificacao_ou_conexao'
    finally:
        if driver is not None:
            driver.detach()  # Nunca usar with: __exit__ do pyjab encerra o processo alvo.
        after = props.read_bytes() if props.exists() else None
        result['configuracao_acessibilidade_preservada'] = before == after
        folder = ROOT / 'logs'
        folder.mkdir(exist_ok=True)
        target = folder / ('diagnostico_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'arquivo': str(target), 'conexao': result.get('conexao'),
                          'controles': len(result['controles']), 'erro_tipo': result.get('erro_tipo')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
