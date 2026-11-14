import json
from pathlib import Path
import subprocess
import sys
import time

from .runtime import RESOURCES
BASE=RESOURCES
sys.path.insert(0,str(BASE/'scripts'))
from backend_empresa import BackendJava
from .runtime import command
from .win_focus import allow_foreground
from .errors import UserError


class PVA(BackendJava):
    def close(self,criteria,folder):
        folder.mkdir(parents=True)
        with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
            p=subprocess.Popen(command('scripts/acessar_lista_escrituracoes.py','--worker','fechar',folder),stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            self.track(p)
            allow_foreground(p.pid)
            try: p.wait(timeout=20)
            except subprocess.TimeoutExpired:
                return {'sucesso':False,'worker_pendente':True,'pid_worker_preservado':p.pid}
        file=folder/'fechar.resultado.json'
        result=json.loads(file.read_text('utf-8')) if file.exists() else {'sucesso':False}
        if result.get('sucesso') and not result.get('erro_tipo'):
            state=self.estado(criteria,folder/'confirmar_fechamento')
            result['fechamento_confirmado']=safe_empty(state)
        return result

    def report(self,case,folder):
        from poc_ponta_a_ponta import supervisor
        return supervisor(folder,case,process_observer=self.track)

    def catalog(self,folder):
        folder.mkdir(parents=True)
        with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
            p=subprocess.Popen(command('app/pva_worker.py',folder,'--expandir-categorias'),
                stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            self.track(p)
            try: p.wait(timeout=25)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=5);raise TimeoutError('Leitura da árvore excedeu o prazo.')
        result=json.loads((folder/'resultado.json').read_text('utf-8'))
        if not result.get('sucesso'):
            messages={'modal_aberta':'Feche o diálogo aberto no PVA antes de atualizar a árvore.',
                'arvore_ausente_ambigua':'Abra uma escrituração e deixe a aba Relatórios disponível no PVA.',
                'pva_ausente_ambiguo':'Não foi encontrada uma única janela principal do PVA.',
                'expansao_nao_confirmada':'Uma categoria não confirmou a expansão. Nenhum relatório foi aberto.'}
            raise UserError(messages.get(result.get('motivo'),'Não foi possível acessar a árvore Java. Use Acesso ao PVA para preparar a comunicação.'))
        if result.get('nos_sem_nome_omitidos'):
            raise UserError('Ainda há categorias sem nomes acessíveis. O catálogo anterior foi preservado; nenhum relatório foi aberto.')
        return result['caminhos']


def safe_empty(state):
    return (state.get('aberta') is False and state.get('pode_abrir') is True and bool(state.get('janela'))
            and not any(state.get(k) for k in ('erro_tipo','timeout','modal_aberta')))


def correct(state):
    return (state.get('aberta') is True and state.get('rodape_lido') is True
            and state.get('identidade_aberta_confirmada') is True
            and not any(state.get(k) for k in ('erro_tipo','timeout','modal_aberta')))
