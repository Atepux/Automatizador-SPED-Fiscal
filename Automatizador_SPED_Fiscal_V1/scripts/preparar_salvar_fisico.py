"""Preparacao somente: calcula/valida o alvo Java, sem clicar nem mudar foco.

Nao cria driver. Para teste futuro autorizado, receber o botao do visualizador
apos resolver e ativar Operacoes Proprias. A funcao nunca aciona Salvar.
"""
import inspect
import json


def preparar_alvo(driver, button):
    import win32gui as gui
    import win32process
    hwnd = driver.hwnd
    if gui.GetClassName(hwnd) != 'SunAwtFrame':
        raise RuntimeError('Exigida janela principal, nao dialogo de confirmacao')
    if not gui.GetWindowText(hwnd).startswith('Sped Fiscal - EFD ICMS/IPI'):
        raise RuntimeError('Janela principal nao corresponde ao PVA')
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if driver.pid != pid or button.hwnd != hwnd:
        raise RuntimeError('Driver e botao devem pertencer a mesma janela do PVA')
    dialogs = []
    def check(h, _):
        if gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == pid and gui.GetClassName(h) in {'SunAwtDialog', '#32770'}:
            dialogs.append(h)
    gui.EnumWindows(check, None)
    if dialogs:
        raise RuntimeError('Dialogo ja aberto: nao acionar novamente')
    if button.role_en_us != 'push button' or not (button.name.strip() == 'Salvar' or button.description.strip() == 'Salvar'):
        raise RuntimeError('Alvo nao identificado semanticamente como Salvar')
    if not {'enabled', 'visible', 'showing'}.issubset(button.states_en_us):
        raise RuntimeError('Botao nao esta habilitado e visivel')
    # click(simulate=True) chama foreground internamente; evitar que a versao
    # instalada envie espaco a outra janela ao tentar obter o foco.
    if gui.IsIconic(hwnd) or gui.GetForegroundWindow() != hwnd:
        raise RuntimeError('PVA deve estar restaurado e em primeiro plano')
    bounds = button.bounds
    if bounds['width'] <= 0 or bounds['height'] <= 0:
        raise RuntimeError('Limites Java invalidos')
    point = button._physical_point(*button._click_point())
    under = gui.WindowFromPoint(point)
    if under != hwnd and gui.GetAncestor(under, 2) != hwnd:
        raise RuntimeError('Outro aplicativo ou janela obstrui o ponto dinamico')
    return {'pid_pva': pid, 'hwnd': hwnd, 'bounds_java': bounds,
            'ponto_fisico_dinamico': list(point), 'clique_executado': False}


def requisitos_estaticos():
    # Importar a classe nao inicializa Service/JABDriver nem acessa o PVA.
    from pyjab.jabelement import JABElement
    from pyjab.common.win32utils import Win32Utils
    signature = inspect.signature(JABElement.click)
    return {'click_tem_parametro_simulate': 'simulate' in signature.parameters,
            'conversao_coordenadas_disponivel': callable(getattr(JABElement, '_physical_point', None)),
            'calculo_centro_disponivel': callable(getattr(JABElement, '_click_point', None)),
            'entrada_mouse_disponivel': callable(getattr(Win32Utils, '_click_mouse', None)),
            'acesso_ao_PVA_executado': False, 'clique_executado': False}


if __name__ == '__main__':
    print(json.dumps(requisitos_estaticos(), ensure_ascii=False))
