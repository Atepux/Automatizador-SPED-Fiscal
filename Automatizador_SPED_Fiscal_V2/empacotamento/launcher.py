"""Arquivo unico: prepara runtime local por usuario e abre o aplicativo."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import zipfile


def main():
    resources=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
    metadata=json.loads((resources/'pacote.json').read_text('utf-8'))
    payload=resources/'programa.zip'
    if hashlib.sha256(payload.read_bytes()).hexdigest()!=metadata['sha256']:raise RuntimeError('Pacote danificado.')
    data=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'AutomatizadorSPEDFiscal'/'V2'
    runtime=data/'programa'/metadata['sha256'][:16];exe=runtime/'SpedFiscal.exe'
    if not (runtime/'instalacao_concluida.json').is_file():
        staging=runtime.with_name(runtime.name+'.novo_'+uuid4().hex[:8]);staging.mkdir(parents=True)
        with zipfile.ZipFile(payload) as z:
            for name in z.namelist():
                target=(staging/name).resolve()
                if not target.is_relative_to(staging.resolve()):raise RuntimeError('Pacote inválido.')
            z.extractall(staging)
        if runtime.exists():
            # Outra instancia pode ter terminado a instalacao; nunca apagar runtime.
            if not (runtime/'instalacao_concluida.json').is_file():
                runtime=runtime.with_name(runtime.name+'_'+uuid4().hex[:8])
        if not runtime.exists():staging.rename(runtime)
        exe=runtime/'SpedFiscal.exe'
        (runtime/'instalacao_concluida.json').write_text(json.dumps({'sha256':metadata['sha256']}),encoding='utf-8')
    env={**os.environ,'PYINSTALLER_RESET_ENVIRONMENT':'1'}
    args=[str(exe),*sys.argv[1:]]
    p=subprocess.Popen(args,cwd=runtime,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
    if len(sys.argv)>1:return p.wait(timeout=90)
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        if len(sys.argv)>2 and sys.argv[1]=='--autoteste':
            Path(sys.argv[2]).write_text(json.dumps({'sucesso':False,'erro_tipo':type(exc).__name__,'PVA_acessado':False}),encoding='utf-8')
        else:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,'Não foi possível iniciar. Copie o arquivo novamente e tente abrir em uma pasta local.','Automatizador SPED Fiscal',0x10)
        sys.exit(1)
