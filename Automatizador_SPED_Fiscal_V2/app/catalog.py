import hashlib
import json
import re
from pathlib import Path
from .domain import excluded,filename
from .runtime import DATA,RESOURCES

BASE=DATA


def load_catalog():
    return [{**r,'opcional':False} for r in json.loads((RESOURCES/'config/catalogo_gui.json').read_text('utf-8'))['relatorios']]


def discovered(paths,existing):
    by_path={tuple(r['caminho_pva']):r for r in existing}
    for path in paths:
        if len(path)<2 or path[0]!='Escrituração Fiscal' or excluded(path): continue
        if tuple(path) in by_path: continue
        name=path[-1]
        special=name in {'Assinatura','Dados da Escrituração'}
        pdf=name+'.pdf'
        try: filename(pdf)
        except ValueError:
            pdf=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',name).strip(' .')+'.pdf'
            try:filename(pdf)
            except ValueError:special=True;pdf='Nome a definir.pdf'
        by_path[tuple(path)]={'id':'pva_'+hashlib.sha256(json.dumps(path,ensure_ascii=False).encode()).hexdigest()[:16],
            'caminho_pva':path,'nome_original':name,'nome_pdf':pdf,'exibir_subrelatorios':False,
            'opcional':False,'suporte':'especial_nao_suportado' if special else 'generico',
            'marcadores':{}}
    return list(by_path.values())
