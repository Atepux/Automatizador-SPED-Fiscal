"""Adaptador Java isolado em processos. Nao contem comando de fechamento."""
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from execucao_runtime import command,RESOURCES,allow_foreground

BASE = RESOURCES


def locate_menu(root,children):
    """A barra principal basta; nunca percorrer o visualizador de PDFs."""
    def find(el,depth=0):
        if depth>15: raise RuntimeError('limite_profundidade_menu')
        if el.role_en_us=='menu bar':
            matches=[c for c in children(el) if c.role_en_us=='menu' and c.name=='Escrituração Fiscal']
            if len(matches)!=1: raise RuntimeError('menu_ambiguo')
            return matches[0]
        if el.role_en_us in {'tree','table','list','text','tool bar','viewport','scroll pane'}: return None
        for c in children(el):
            result=find(c,depth+1)
            if result is not None:return result
        return None
    menu=find(root)
    if menu is None:raise RuntimeError('menu_ausente')
    return menu


def estado_worker(criterios):
    from pyjab.common.service import Service
    from pyjab.jabdriver import JABDriver
    from pyjab.jabelement import JABElement
    from modal_concorrente import state
    from acessar_lista_escrituracoes import dialogs
    from rodape_escrituracao import read_footer
    logging.disable(logging.CRITICAL)
    def block(self): raise RuntimeError('configuracao_bloqueada')
    Service.__wrapped__.enable_bridge = block
    driver = None; held = []
    try:
        hwnd,pid,_ = state()
        result = {'janela':[hwnd,pid],'modal_aberta':bool(dialogs(pid))}
        if result['modal_aberta']: return result
        cfg = tomllib.loads((BASE/'config/diagnostico.toml').read_text('utf-8'))
        driver = JABDriver(hwnd=hwnd,bridge_dll=cfg['bridge_dll'],timeout=5)
        def children(el):
            if len(held)>1000: raise RuntimeError('limite_controles')
            out = []
            for i in range(el.children_count):
                ctx = driver.bridge.getAccessibleChildFromContext(driver.vmid,el.accessible_context,i)
                if ctx:
                    child = JABElement(driver.bridge,hwnd,driver.vmid,ctx)
                    held.append(child); out.append(child)
            return out
        items = children(locate_menu(driver.root_element,children))
        commands = {}
        for name in ('Abrir','Fechar'):
            found = [c for c in items if c.role_en_us=='menu item' and c.name==name]
            if len(found)!=1: raise RuntimeError('comando_ambiguo')
            commands[name] = 'enabled' in found[0].states_en_us
        if commands == {'Abrir':True,'Fechar':False}:
            # Tambem conferir o rodape: evidencia contraditoria bloqueia.
            footer = read_footer(driver,criterios)
            if footer['rodape_lido']: raise RuntimeError('estado_contraditorio')
            result.update(aberta=False,pode_abrir=True)
        elif commands == {'Abrir':False,'Fechar':True}:
            result.update(aberta=True,pode_abrir=False)
            result.update(read_footer(driver,criterios))
        else: raise RuntimeError('estado_ambiguo')
        result['modal_aberta'] = bool(dialogs(pid))
        return result
    finally:
        for el in reversed(held):
            try: el.release_jabelement()
            except Exception: pass
        if driver: driver.detach()


class BackendJava:
    def __init__(self):
        self.children=[]

    def track(self,process):
        self.children.append(process)

    def pending_workers(self):
        return [process.pid for process in self.children if process.poll() is None]

    def _worker(self,mode,criteria,folder,timeout):
        folder.mkdir(parents=True)
        with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
            p = subprocess.Popen(command('scripts/backend_empresa.py','--worker',mode,folder),
                stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW)
            self.track(p)
            allow_foreground(p.pid)
            try: p.communicate(json.dumps(criteria),timeout=timeout)
            except subprocess.TimeoutExpired:
                p.kill(); p.communicate(timeout=5)
                return {'timeout':True,'identidade_aberta_confirmada':False}
        path = folder/'resultado.json'
        return json.loads(path.read_text('utf-8')) if path.exists() else {'erro_tipo':'WorkerSemResultado'}

    def estado(self,criteria,folder):
        return self._worker('estado',criteria,folder,25)

    def identificar(self):
        # Identificacao aprovada da V1, importada exclusivamente da copia V2.
        sys.path.insert(0,str(BASE))
        from geracao_v1 import identificar_pva
        return identificar_pva()

    def abrir(self,criteria,identity,folder):
        from modal_concorrente import state
        from acessar_lista_escrituracoes import dialogs
        folder.mkdir(parents=True)
        if list(state()[:2]) != list(identity) or dialogs(identity[1]):
            return {'erro_tipo':'EstadoMudou'}
        opener_folder = folder/'lista'; opener_folder.mkdir()
        opener = None
        result = {}
        try:
            with (opener_folder/'stdout.txt').open('w') as out,(opener_folder/'stderr.txt').open('w') as err:
                opener = subprocess.Popen(command('scripts/acessar_lista_escrituracoes.py','--worker','abrir',opener_folder),stdout=out,stderr=err,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                self.track(opener)
                allow_foreground(opener.pid)
                until = time.monotonic()+15
                while time.monotonic()<until:
                    if list(state()[:2]) != list(identity): raise RuntimeError('janela_mudou')
                    current = dialogs(identity[1])
                    if current:
                        if len(current)!=1 or current[0]['titulo']!='Abrir Escrituração' or current[0]['classe']!='SunAwtDialog':
                            raise RuntimeError('modal_desconhecida')
                        break
                    if opener.poll() is not None: raise RuntimeError('abertura_lista_falhou')
                    time.sleep(.05)
                else: raise TimeoutError('lista_nao_abriu')
                # Abridor continua vivo durante a conexao/selecao Java.
                result = self._worker('selecionar',criteria,folder/'selecao',55)
        except Exception as exc:
            result = {'erro_tipo':type(exc).__name__}
        finally:
            (opener_folder/'inspecao_concluida.signal').write_text('concluido',encoding='utf-8')
            if opener:
                try: opener.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    result.update(worker_pendente=True,pid_worker_preservado=opener.pid)
                # Nunca encerrar opener/PVA por conta propria.
                if opener.poll() is not None:
                    path = opener_folder/'abrir.resultado.json'
                    if opener.returncode != 0 or not path.exists() or not json.loads(path.read_text('utf-8')).get('sucesso'):
                        result['erro_tipo'] = 'AbridorNaoConfirmado'
        return result


def main():
    criteria = json.load(sys.stdin)
    mode,folder = sys.argv[2],Path(sys.argv[3])
    if mode=='selecionar':
        from selecao_escrituracao import worker
        worker(criteria,folder,'selecionar'); return
    try: result = estado_worker(criteria)
    except Exception as exc:
        import traceback
        result = {'erro_tipo':type(exc).__name__,
            'pilha':[{'funcao':f.name,'linha':f.lineno} for f in traceback.extract_tb(exc.__traceback__)]}
        if str(exc) in {'limite_controles','limite_profundidade_menu','menu_ambiguo','menu_ausente','comando_ambiguo','estado_contraditorio','estado_ambiguo','pva_ausente_ambiguo','limite_rodape'}:
            result['motivo']=str(exc)
    (folder/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__': main()
