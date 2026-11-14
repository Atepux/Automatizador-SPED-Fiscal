"""Teste do executavel/IPC, sem acesso ao PVA."""
import json,sys,struct
from pathlib import Path
import pyjab,win32gui,win32api,pythoncom,openpyxl,xlrd,pymupdf

if __name__=='__main__':
    value=json.load(sys.stdin)
    folder=Path(sys.argv[1]);folder.mkdir(parents=True,exist_ok=True)
    result={'worker':True,'entrada_recebida':value=={'teste':'ok'},'bits':struct.calcsize('P')*8,'PVA_acessado':False}
    (folder/'resultado.json').write_text(json.dumps(result),encoding='utf-8')
    print('worker offline concluido',flush=True)
