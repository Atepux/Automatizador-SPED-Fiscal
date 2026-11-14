import json
from pathlib import Path
import runpy
import sys
from app.runtime import RESOURCES,setup_streams,prepare_bridge

ALLOWED={'scripts/backend_empresa.py','scripts/acessar_lista_escrituracoes.py','scripts/poc_ponta_a_ponta.py',
         'app/pva_worker.py','app/offline_worker.py'}


def dispatch():
    setup_streams()
    if len(sys.argv)<3 or sys.argv[1]!='--sped-worker' or sys.argv[2] not in ALLOWED:
        raise ValueError('worker_nao_autorizado')
    script=RESOURCES/sys.argv[2]
    sys.path.insert(0,str(RESOURCES));sys.path.insert(0,str(RESOURCES/'scripts'))
    prepare_bridge()
    sys.argv=[str(script),*sys.argv[3:]]
    runpy.run_path(str(script),run_name='__main__')


if __name__=='__main__':dispatch()
