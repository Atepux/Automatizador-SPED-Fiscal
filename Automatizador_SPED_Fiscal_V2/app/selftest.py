import json
from pathlib import Path
import subprocess
import sys
import tempfile
from .runtime import command,validate_resources


def simulate_companies(root):
    from .catalog import load_catalog
    from .storage import Store
    from .processing import Processor
    import pymupdf
    store=Store(root/'simulacao.sqlite3',load_catalog())
    numbers=[]
    for base in ('001234560001','112345670001'):
        value=base
        for weights in ([5,4,3,2,9,8,7,6,5,4,3,2],[6,5,4,3,2,9,8,7,6,5,4,3,2]):
            remainder=sum(int(n)*w for n,w in zip(value,weights))%11
            value+=str(0 if remainder<2 else 11-remainder)
        numbers.append(value);store.add(value,'Empresa de teste '+str(len(numbers)))
        rows=store.settings(value)
        for row in rows:row['selecionado']=row.get('suporte')=='aprovado'
        store.save_settings(value,rows)
    class FakePVA:
        active=None
        closes=0
        fail_next=False
        def estado(self,criteria,folder):
            if self.active is None:return {'aberta':False,'pode_abrir':True,'janela':[1,2]}
            return {'aberta':True,'janela':[1,2],'rodape_lido':True,'identidade_aberta_confirmada':self.active==criteria['cnpj']}
        def abrir(self,criteria,identity,folder):
            self.active=criteria['cnpj']
            return {'correspondencia_unica':True,'selecao_confirmada':True,'ok_tentativas':1,'identidade_aberta_confirmada':True}
        def identificar(self):return (1,2)
        def report(self,case,folder):
            if self.fail_next:
                self.fail_next=False
                return {'sucesso':False}
            doc=pymupdf.open();doc.new_page();doc.save(case['destino']);doc.close()
            return {'sucesso':True}
        def close(self,criteria,folder):
            self.active=None;self.closes+=1
            return {'sucesso':True,'fechamento_confirmado':True}
    backend=FakePVA()
    jobs=[{**c,'relatorios':store.settings(c['cnpj'])} for c in store.companies()]
    result=Processor(backend,temporary_root=root/'temporarios').run(jobs,'10/2026',root/'saida',root/'simulacao')
    # Nova tentativa apos falha: mesmo backend e mesma escrituração aberta.
    retry_backend=FakePVA();retry_backend.fail_next=True
    failed=Processor(retry_backend,temporary_root=root/'retry_temp').run(jobs,'10/2026',root/'retry_saida',root/'retry_falha')
    from .locks import release_owned
    import os
    locks=root/'travas';locks.mkdir()
    for name in ('automacao_ativa.lock','multiempresas_ativa.lock'):
        (locks/name).write_text(json.dumps({'pid':os.getpid()}),encoding='utf-8')
    unlocked=release_owned(locks,os.getpid(),[])
    retried=Processor(retry_backend,temporary_root=root/'retry_temp').run(jobs,'10/2026',root/'retry_saida',root/'retry_ok')
    retry_ok=(not failed['sucesso'] and unlocked and retried['sucesso']
              and retried['empresas'][0].get('escrituracao_reutilizada') is True)
    return {'sucesso':result['sucesso'],'pdfs':result['pdfs'],'empresas':len(result['empresas']),
            'fechamentos':backend.closes,'nova_tentativa_apos_falha':retry_ok,'PVA_acessado':False}


def main():
    from .storage import Store
    from .catalog import load_catalog
    from .gui import App
    import tkinter as tk
    import pymupdf
    output=Path(sys.argv[2]);result={'sucesso':False,'PVA_acessado':False}
    try:
        result['recursos']=validate_resources()
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);store=Store(root/'teste.sqlite3',load_catalog())
            window=tk.Tk();window.withdraw()
            try:
                app=App(window,store);window.update_idletasks()
                result['telas']=len(app.tabs.tabs())
                import win32gui,win32con
                from .branding import create_toplevel
                secondary=create_toplevel(window);window.deiconify();window.update()
                result['icone_janelas']=all(win32gui.SendMessage(win32gui.GetParent(w.winfo_id()),
                    win32con.WM_GETICON,1,0) for w in (window,secondary))
                secondary.destroy();window.withdraw()
            finally:window.destroy()
            doc=pymupdf.open();doc.new_page();doc.save(root/'teste.pdf');doc.close()
            with pymupdf.open(root/'teste.pdf') as doc:result['pdf']=doc.page_count==1
            folder=root/'worker';folder.mkdir()
            with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
                p=subprocess.Popen(command('app/offline_worker.py',folder),stdin=subprocess.PIPE,
                    stdout=out,stderr=err,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
                try:p.communicate('{"teste":"ok"}',timeout=35)
                except subprocess.TimeoutExpired:p.kill();p.communicate(timeout=5);raise TimeoutError()
            if (folder/'resultado.json').exists():result['auxiliar']=json.loads((folder/'resultado.json').read_text('utf-8'))
            result['saida_auxiliar']=(folder/'stdout.txt').read_text('utf-8').strip()
            result['erro_auxiliar']=(folder/'stderr.txt').read_text('utf-8').strip()
            result['simulacao']=simulate_companies(root)
            result['sucesso']=(result['telas']==3 and result['icone_janelas'] and result['pdf'] and p.returncode==0
                              and result.get('auxiliar',{}).get('entrada_recebida') is True
                              and result['simulacao']['sucesso'] and result['simulacao']['pdfs']==16
                              and result['simulacao']['nova_tentativa_apos_falha'])
    except Exception as exc:
        import traceback
        result['erro_tipo']=type(exc).__name__;result['pilha']=traceback.format_exc()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if result['sucesso'] else 1
