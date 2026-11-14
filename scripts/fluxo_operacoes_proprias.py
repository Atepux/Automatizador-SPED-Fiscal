"""POC de um relatorio fixo: selecao Java, exportacao unica, verificacao local."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
import tomllib
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TARGET = ['Escrituração Fiscal', 'Relatórios de Registros Fiscais',
          'Apuração do ICMS', 'Operações Próprias']
DEST = ROOT / 'saida/TESTE_FICTICIO/teste_fluxo_operacoes_proprias.pdf'


def main():
    import win32gui as gui
    import win32process
    import pymupdf
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    logging.disable(logging.CRITICAL)
    cfg = tomllib.loads((ROOT / 'config/diagnostico.toml').read_text('utf-8'))
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    output = logs / ('fluxo_operacoes_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    result = {'data_utc': datetime.now(timezone.utc).isoformat(), 'destino': str(DEST),
              'caminho_relatorio': TARGET, 'sucesso': False, 'acoes': [],
              'criterio_selecao': 'estado selected; atualizacao automatica informada pelo usuario'}
    def record():
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    def stop(reason):
        result['interrupcao'] = reason
        raise RuntimeError(reason)
    def once(name, action):
        result['acoes'].append({'acao': name, 'estado': 'tentativa_registrada'})
        record()
        action()
        result['acoes'][-1]['estado'] = 'chamada_retornou'
        record()
    props = Path.home() / '.accessibility.properties'
    before = props.read_bytes() if props.exists() else None
    def block(self):
        raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge = block
    drivers, held = [], []
    stage = 'preparacao'
    try:
        if DEST.exists():
            stop('destino_ja_existe')
        DEST.parent.mkdir(parents=True, exist_ok=True)
        def windows():
            found = []
            gui.EnumWindows(lambda h, _: found.append(h) if gui.IsWindowVisible(h) else None, None)
            return found
        roots = [h for h in windows() if gui.GetWindowText(h).startswith(cfg['titulo_prefixo'])]
        if len(roots) != 1:
            stop('pva_ausente_ou_ambiguo')
        main_hwnd = roots[0]
        _, pid = win32process.GetWindowThreadProcessId(main_hwnd)
        result.update(pid=pid, hwnd=main_hwnd)
        def owned():
            return {h for h in windows() if win32process.GetWindowThreadProcessId(h)[1] == pid}
        baseline = owned()
        if any(gui.GetClassName(h) in {'SunAwtDialog', '#32770'} for h in baseline):
            stop('dialogo_inicial_inesperado')
        def connect(hwnd):
            d = JABDriver(hwnd=hwnd, bridge_dll=cfg['bridge_dll'], timeout=5)
            drivers.append(d)
            return d
        driver = connect(main_hwnd)
        def children(d, el):
            count = el.children_count
            if count > 700:
                stop('limite_filhos')
            out = []
            for i in range(count):
                c = d.bridge.getAccessibleChildFromContext(d.vmid, el.accessible_context, i)
                if c:
                    child = JABElement(d.bridge, d.hwnd, d.vmid, c)
                    held.append(child)
                    out.append((i, child))
            return out
        def scan(d, predicate):
            matches, count = [], 0
            def walk(el, depth=0, reports=False):
                nonlocal count
                count += 1
                if depth > 24 or count > 900:
                    stop('limite_inspecao')
                role = el.role_en_us
                reports = reports or (role == 'page tab' and el.name == 'Relatórios')
                if predicate(el, reports):
                    matches.append(el)
                if role in {'tree','text','password text','list','table','menu bar'}:
                    return
                for _, child in children(d, el):
                    walk(child, depth+1, reports)
            walk(d.root_element)
            return matches
        stage = 'resolver_caminho'
        trees = scan(driver, lambda e,s: s and e.role_en_us == 'tree')
        if len(trees) != 1:
            stop('arvore_ambigua')
        parent = trees[0]
        for pos, name in enumerate(TARGET):
            matches = [(i,e) for i,e in children(driver,parent) if e.name == name]
            if len(matches) != 1:
                stop('segmento_ausente_ou_ambiguo')
            index, node = matches[0]
            if not {'visible','showing'}.issubset(node.states_en_us):
                stop('no_nao_visivel')
            if pos < len(TARGET)-1:
                if 'expanded' not in node.states_en_us:
                    stop('pai_recolhido_nao_expandir')
                parent = node
        if not parent.accessible_selection:
            stop('pai_sem_selecao_acessivel')
        result['selecionado_antes'] = 'selected' in node.states_en_us
        # Trava desta nova autorizacao: nunca reutiliza/remove travas anteriores.
        with (logs / 'fluxo_operacoes_acionado.lock').open('x', encoding='utf-8') as f:
            f.write(str(output))
        stage = 'selecionar'
        once('selecionar_operacoes_proprias', lambda: driver.bridge.addAccessibleSelectionFromContext(
            driver.vmid, parent.accessible_context, index))
        deadline = time.monotonic()+5
        while True:
            driver._pump_messages()
            if owned()-baseline:
                stop('janela_inesperada_apos_selecao')
            if 'selected' in node.states_en_us:
                break
            if time.monotonic() > deadline:
                stop('selecao_nao_confirmada')
            time.sleep(.25)
        result['selected_confirmado'] = True
        stage = 'aguardar_visualizador'
        # Janela de espera, sem repetir selecao. O titulo acessivel nao e requisito.
        for _ in range(20):
            driver._pump_messages()
            if owned()-baseline:
                stop('janela_inesperada_carregamento')
            time.sleep(.25)
        result['espera_visualizador_segundos'] = 5
        def is_save(e, _):
            return e.role_en_us == 'push button' and (e.name.strip().casefold() == 'salvar'
                or e.description.strip().casefold() == 'salvar') and 'showing' in e.states_en_us
        saves = scan(driver, is_save)
        if len(saves) != 1 or 'enabled' not in saves[0].states_en_us:
            stop('salvar_visualizador_nao_univoco_ou_desabilitado')
        result['botao_visualizador_identificado_por'] = 'papel push button e nome/descricao Salvar'
        stage = 'abrir_salvar'
        once('abrir_dialogo_salvar', lambda: saves[0]._do_accessible_action('click'))
        deadline = time.monotonic()+10
        save_hwnd = None
        while time.monotonic() < deadline:
            driver._pump_messages()
            new = owned()-baseline
            expected = {h for h in new if gui.GetWindowText(h).strip().casefold() in {'salvar','save','salvar como','save as'}
                        and gui.GetClassName(h) == 'SunAwtDialog'}
            if new-expected or len(expected)>1:
                stop('janela_inesperada_ao_abrir_salvar')
            if len(expected)==1:
                save_hwnd = next(iter(expected))
                break
            time.sleep(.25)
        if save_hwnd is None:
            stop('salvar_nao_abriu_sem_repetir')
        stage = 'preencher_destino'
        sd = connect(save_hwnd)
        fields = scan(sd, lambda e,s: e.role_en_us == 'text' and e.name.strip().casefold() == 'nome do arquivo:')
        buttons = scan(sd, lambda e,s: e.role_en_us == 'push button' and e.name.strip().casefold() == 'salvar')
        if len(fields)!=1 or len(buttons)!=1:
            stop('controles_salvar_ambiguos')
        field, button = fields[0], buttons[0]
        if not {'enabled','editable','showing'}.issubset(field.states_en_us) or 'enabled' not in button.states_en_us:
            stop('controles_nao_habilitados')
        once('preencher_caminho', lambda: field.send_text(str(DEST), simulate=False, wait_for_text_update=False))
        result['caminho_confirmado_por_leitura'] = field.text == str(DEST)
        if not result['caminho_confirmado_por_leitura']:
            stop('caminho_divergente')
        allowed = baseline | {save_hwnd}
        if owned()-allowed:
            stop('janela_inesperada_antes_gravacao')
        if DEST.exists():
            stop('destino_passou_a_existir')
        stage = 'salvar_unico_pdf'
        once('confirmar_salvar', lambda: button._do_accessible_action('click'))
        deadline, previous, stable = time.monotonic()+30, None, 0
        while time.monotonic()<deadline:
            driver._pump_messages()
            if owned()-allowed:
                stop('janela_inesperada_apos_gravacao')
            if DEST.is_file():
                st=DEST.stat()
                sig=(st.st_size,st.st_mtime_ns)
                stable=stable+1 if sig==previous and st.st_size>0 else 0
                previous=sig
                if stable>=4 and not gui.IsWindowVisible(save_hwnd):
                    break
            time.sleep(.25)
        else:
            stop('gravacao_nao_concluida_no_prazo')
        stage = 'verificar_pdf'
        result['tamanho_bytes'] = DEST.stat().st_size
        def normalized(s):
            return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',s.casefold())
                                   if not unicodedata.combining(c)).split())
        with pymupdf.open(DEST) as pdf:
            result.update(paginas=pdf.page_count, pdf_abre=True, reparado=pdf.is_repaired)
            if not pdf.is_pdf or pdf.needs_pass or pdf.page_count<1 or pdf.is_repaired:
                stop('pdf_estrutura_invalida')
            markers = {'operacoes_proprias':False, 'apuracao_icms':False}
            for i in range(pdf.page_count):
                page=pdf.load_page(i)
                # Texto tratado apenas em memoria. Nao imprimir/gravar conteudo fiscal.
                text=normalized(page.get_text())
                markers['operacoes_proprias'] |= 'operacoes proprias' in text
                markers['apuracao_icms'] |= 'apuracao do icms' in text
            result['marcadores_conteudo'] = markers
            result['correspondencia_conteudo'] = 'confirmada_por_marcadores' if all(markers.values()) else 'inconclusiva'
        result['sucesso'] = True
    except Exception as exc:
        result.update(erro_tipo=type(exc).__name__, erro_etapa=stage)
    finally:
        for e in reversed(held):
            try:
                e.release_jabelement()
            except Exception:
                pass
        for d in reversed(drivers):
            try:
                d.detach()
            except Exception:
                result['aviso_detach'] = True
        result['configuracao_preservada'] = before == (props.read_bytes() if props.exists() else None)
        result['arquivo_existe'] = DEST.is_file()
        record()
        print(json.dumps({'log':str(output), **result},ensure_ascii=True))


if __name__ == '__main__':
    main()
