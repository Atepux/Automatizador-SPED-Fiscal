"""Arquivar somente travas de processos mortos e sem auxiliares restantes."""
import json
import os
from pathlib import Path
from uuid import uuid4


def pid_alive(pid):
    import win32api,win32event
    try: handle=win32api.OpenProcess(0x100000,False,pid)
    except Exception as exc:
        # ERROR_INVALID_PARAMETER: PID inexistente. Acesso negado nao prova morte.
        return getattr(exc,'winerror',None)!=87
    try:return win32event.WaitForSingleObject(handle,0)!=win32event.WAIT_OBJECT_0
    finally:handle.Close()


def auxiliary_active():
    import win32com.client
    import pythoncom
    pythoncom.CoInitialize()
    try:
        service=win32com.client.GetObject('winmgmts:')
        processes=service.ExecQuery("SELECT ProcessId,CommandLine,Name FROM Win32_Process WHERE Name='python.exe' OR Name='pythonw.exe' OR Name='SpedFiscal.exe'")
        for process in processes:
            if int(process.ProcessId)==os.getpid():continue
            command=process.CommandLine
            if process.Name.casefold()=='spedfiscal.exe' or not command or 'automatizador_sped_fiscal_v2' in command.casefold():return True
        return False
    finally:pythoncom.CoUninitialize()


def recover_stale(logs,alive=pid_alive,auxiliaries=auxiliary_active):
    logs=Path(logs)
    files=[logs/name for name in ('automacao_ativa.lock','multiempresas_ativa.lock','empresa_unica_ativa.lock','execucao_ativa.lock') if (logs/name).exists()]
    if not files:return []
    try:
        owners=[json.loads(path.read_text('utf-8'))['pid'] for path in files]
        if any(type(pid) is not int or pid<=0 or alive(pid) for pid in owners) or auxiliaries():return []
    except Exception:return []
    archived=[]
    for path in files:
        target=path.with_name(path.name+'.revisada_'+uuid4().hex[:8])
        path.rename(target);archived.append(target.name)
    return archived


def release_owned(logs,owner,pending_workers):
    """Falha nao e execucao ativa. Só liberar depois dos filhos terminarem."""
    if pending_workers:return False
    logs=Path(logs)
    try:
        for name in ('automacao_ativa.lock','multiempresas_ativa.lock'):
            file=logs/name
            if file.exists() and json.loads(file.read_text('utf-8')).get('pid')==owner:
                file.unlink()
        return not any((logs/name).exists() for name in ('automacao_ativa.lock','multiempresas_ativa.lock'))
    except (OSError,ValueError):return False
