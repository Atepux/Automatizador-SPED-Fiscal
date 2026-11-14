"""POC autorizada: uma unica acao Salvar; sem repeticao e sem extrair conteudo."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'saida' / 'TESTE_FICTICIO' / 'relatorio_teste.pdf'


def main():
    import win32gui
    import win32process
    import pymupdf
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    cfg = tomllib.loads((ROOT / 'config/diagnostico.toml').read_text('utf-8'))
    folder = ROOT / 'logs'
    folder.mkdir(exist_ok=True)
    output = folder / ('salvamento_unico_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    result = {'data_utc': datetime.now(timezone.utc).isoformat(), 'destino': str(DEST),
              'acoes_salvar_tentadas': 0, 'sucesso': False}
    def record():
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    def stop(reason):
        result['motivo_interrupcao'] = reason
        raise RuntimeError(reason)
    props = Path.home() / '.accessibility.properties'
    before = props.read_bytes() if props.exists() else None
    def block(self):
        raise RuntimeError('configuracao_acessibilidade_bloqueada')
    Service.__wrapped__.enable_bridge = block
    driver, held = None, []
    stage = 'preparacao'
    try:
        if DEST.exists():
            stop('destino_ja_existe')
        if (folder / 'salvar_unico_acionado.lock').exists():
            stop('tentativa_anterior_registrada_nao_repetir')
        DEST.parent.mkdir(parents=True, exist_ok=True)
        def windows():
            found = []
            win32gui.EnumWindows(lambda h, _: found.append(h) if win32gui.IsWindowVisible(h) else None, None)
            return found
        visible = windows()
        roots = [h for h in visible if win32gui.GetWindowText(h).startswith(cfg['titulo_prefixo'])]
        if len(roots) != 1:
            stop('janela_pva_ambigua_ou_ausente')
        _, pid = win32process.GetWindowThreadProcessId(roots[0])
        def owned():
            return {h for h in windows() if win32process.GetWindowThreadProcessId(h)[1] == pid}
        baseline = owned()
        saves = [h for h in baseline if win32gui.GetWindowText(h).strip().lower() in {'salvar', 'save', 'salvar como', 'save as'}]
        if len(saves) != 1:
            stop('janela_salvar_ambigua_ou_ausente')
        hwnd = saves[0]
        if any(h != hwnd and win32gui.GetClassName(h) in {'SunAwtDialog', '#32770'} for h in baseline):
            stop('outro_dialogo_ja_aberto')
        result.update(pid=pid, hwnd_salvar=hwnd, classe=win32gui.GetClassName(hwnd))
        stage = 'inspecao'
        driver = JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5)
        fields, buttons = [], []
        count = 0
        def visit(el, depth):
            nonlocal count
            count += 1
            if count > 180:
                stop('limite_inspecao')
            role, name = el.role_en_us, el.name.strip().lower()
            if role == 'text' and name in {'nome do arquivo:', 'nome do arquivo', 'file name:', 'file name'}:
                fields.append(el)
            if role == 'push button' and name in {'salvar', 'save'}:
                buttons.append(el)
            if depth >= 12 or role in {'text', 'password text', 'list', 'table', 'tree'}:
                return
            for i in range(el.children_count):
                context = driver.bridge.getAccessibleChildFromContext(driver.vmid, el.accessible_context, i)
                if context:
                    child = JABElement(driver.bridge, hwnd, driver.vmid, context)
                    held.append(child)
                    visit(child, depth + 1)
        visit(driver.root_element, 0)
        if len(fields) != 1 or len(buttons) != 1:
            stop('campo_ou_botao_nao_univoco')
        field, button = fields[0], buttons[0]
        if not {'enabled', 'editable', 'showing'}.issubset(field.states_en_us):
            stop('campo_nao_editavel_visivel')
        if not {'enabled', 'showing'}.issubset(button.states_en_us):
            stop('botao_nao_habilitado_visivel')
        stage = 'preenchimento'
        field.send_text(str(DEST), simulate=False, wait_for_text_update=False)
        driver._pump_messages()
        result['caminho_confirmado_por_leitura'] = field.text == str(DEST)
        if not result['caminho_confirmado_por_leitura']:
            stop('leitura_diverge_do_caminho')
        if owned() - baseline:
            stop('janela_inesperada_antes_de_salvar')
        if DEST.exists():
            stop('destino_existe_antes_do_acionamento')
        stage = 'acao_salvar'
        # Trava exclusiva persistente antes da acao: nunca repetir numa nova execucao.
        with (folder / 'salvar_unico_acionado.lock').open('x', encoding='utf-8') as lock:
            lock.write(str(output))
        result['acoes_salvar_tentadas'] = 1
        record()
        button._do_accessible_action('click')
        stage = 'aguardar_gravacao'
        deadline, previous, stable = time.monotonic() + 30, None, 0
        while time.monotonic() < deadline:
            driver._pump_messages()
            new = owned() - baseline
            if new:
                result['janelas_inesperadas'] = [{'hwnd': h, 'classe': win32gui.GetClassName(h)} for h in new]
                stop('janela_inesperada_apos_salvar')
            if DEST.is_file():
                stat = DEST.stat()
                signature = (stat.st_size, stat.st_mtime_ns)
                stable = stable + 1 if signature == previous and stat.st_size > 0 else 0
                previous = signature
                if stable >= 4 and not win32gui.IsWindowVisible(hwnd):
                    break
            time.sleep(0.25)
        else:
            stop('tempo_limite_gravacao_sem_repeticao')
        stage = 'verificacao_pdf'
        result['tamanho_bytes'] = DEST.stat().st_size
        with pymupdf.open(DEST) as pdf:
            result.update(pdf_abre=True, formato_pdf=pdf.is_pdf, paginas=pdf.page_count,
                          reparado=pdf.is_repaired, exige_senha=bool(pdf.needs_pass))
            # Carrega todas as paginas sem extrair texto, imagens ou metadados fiscais.
            if pdf.needs_pass or not pdf.is_pdf or pdf.page_count < 1 or pdf.is_repaired:
                stop('pdf_nao_passou_verificacao')
            for index in range(pdf.page_count):
                pdf.load_page(index)
        result.update(sucesso=True, janela_salvar_fechada=not bool(win32gui.IsWindowVisible(hwnd)))
    except Exception as exc:
        result.update(erro_tipo=type(exc).__name__, erro_etapa=stage)
    finally:
        for el in reversed(held):
            try:
                el.release_jabelement()
            except Exception:
                pass
        if driver:
            try:
                driver.detach()
            except Exception:
                result['desconexao_com_aviso'] = True
        result['configuracao_acessibilidade_preservada'] = before == (props.read_bytes() if props.exists() else None)
        result['arquivo_existe'] = DEST.is_file()
        record()
        print(json.dumps({'log': str(output), **result}, ensure_ascii=True))


if __name__ == '__main__':
    main()
