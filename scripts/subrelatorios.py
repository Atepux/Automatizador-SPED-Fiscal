"""Regra idempotente de subrelatorios; nao salva nem abre dialogo Salvar."""
from modal_concorrente import critical,log

NAMES={'Exibir subrelatórios...','Exibir subrelatórios…','Exibir subrelatórios'}


def confirmar_checkbox(ler,marcar,allow_change=True):
    before=ler()
    if not before:
        if not allow_change:raise RuntimeError('checkbox_desmarcada_na_confirmacao_final')
        marcar()  # Uma unica acao; sem retry.
    after=ler()
    if after is not True:raise RuntimeError('checkbox_nao_confirmada')
    return {'inicial':before,'final':True,'checked':True,'alterado':not before}


def garantir_subrelatorios(driver,events,allow_change=True):
    from pyjab.jabelement import JABElement
    import win32gui as g
    import win32process
    held=[];count=0;checks=[];saves=[]
    _,pid=win32process.GetWindowThreadProcessId(driver.hwnd)
    def validate_windows():
        unexpected=[]
        def see(h,_):
            if g.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1]==pid and g.GetClassName(h) in {'SunAwtDialog','#32770'}:unexpected.append(h)
        g.EnumWindows(see,None)
        if unexpected:raise RuntimeError('modal_inesperada_subrelatorios')
    def scan(el,depth=0):
        nonlocal count
        count+=1
        if count>900 or depth>24:raise RuntimeError('limite_inspecao_subrelatorios')
        role=el.role_en_us
        if role=='check box' and el.name in NAMES:checks.append(el)
        if role=='push button' and 'showing' in el.states_en_us and (el.name.strip()=='Salvar' or el.description.strip()=='Salvar'):saves.append(el)
        if role in {'tree','list','table','text','password text','menu bar'}:return
        for i in range(min(el.children_count,700)):
            ctx=driver.bridge.getAccessibleChildFromContext(driver.vmid,el.accessible_context,i)
            if ctx:
                c=JABElement(driver.bridge,driver.hwnd,driver.vmid,ctx);held.append(c);scan(c,depth+1)
    def refresh():
        nonlocal count
        for el in reversed(held):el.release_jabelement()
        held.clear();checks.clear();saves.clear();count=0
        context,vmid=driver._get_accessible_context_from_hwnd(driver.hwnd)
        if not context.value or vmid!=driver.vmid:raise RuntimeError('contexto_alterado_subrelatorios')
        root=JABElement(driver.bridge,driver.hwnd,vmid,context);held.append(root)
        scan(root)
        if len(checks)!=1:raise RuntimeError('checkbox_subrelatorios_ausente_ambiguo')
    try:
        validate_windows()
        critical(events,'subrelatorios.localizar',refresh)
        if len(checks)!=1:raise RuntimeError('checkbox_subrelatorios_ausente_ambiguo')
        box=checks[0]
        if not {'enabled','visible','showing'}.issubset(box.states_en_us):raise RuntimeError('checkbox_subrelatorios_indisponivel')
        def read():
            validate_windows();refresh()
            value=checks[0].is_checked()
            log(events,'subrelatorios_leitura',checked=value)
            return value
        result=confirmar_checkbox(read,lambda:critical(events,'subrelatorios.marcar_uma_vez',
            lambda:checks[0]._do_accessible_action()),allow_change)
        save_ready=len(saves)==1 and {'enabled','visible','showing'}.issubset(saves[0].states_en_us)
        if not save_ready:raise RuntimeError('salvar_indisponivel_apos_checkbox')
        result['salvar_habilitado']=True
        log(events,'subrelatorios_confirmado_regra_simples',**result)
        return result
    finally:
        for el in reversed(held):el.release_jabelement()
