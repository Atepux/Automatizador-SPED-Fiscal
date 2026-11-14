"""Identificacao somente de leitura, sem fechar/confirmar janelas adicionais."""


def identificar_janelas(handles,pid_pva):
    import win32gui as g
    import win32process
    rows=[]
    for hwnd in sorted(handles):
        if not g.IsWindow(hwnd):continue
        _,pid=win32process.GetWindowThreadProcessId(hwnd)
        title=g.GetWindowText(hwnd).strip()
        # Titulos podem conter dados fiscais; registrar somente rotulos reconhecidos.
        known=title if title in {'Salvar','Recibo','Recibo de Transmissão','Aviso','Atenção'} else None
        rows.append({'hwnd':hwnd,'pid':pid,'mesmo_pid_pva':pid==pid_pva,
                     'classe':g.GetClassName(hwnd),'owner_hwnd':g.GetWindow(hwnd,4),
                     'visivel':bool(g.IsWindowVisible(hwnd)),
                     'titulo_reconhecido':known,'titulo_omitido':bool(title and known is None),
                     'indicio_recibo_no_titulo':'recibo' in title.casefold()})
    return rows
