"""Coordenacao sequencial; Parar e observado somente fora de salvamentos."""
import contextlib
import csv
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import threading
import time
from .domain import cnpj,period,folder_name,validate_settings,redact
from .pva import safe_empty,correct
from .runtime import DATA
from .errors import UserError


def persist(folder,summary):
    folder.mkdir(parents=True,exist_ok=True)
    clean=redact(summary)
    temporary=folder/'resumo.tmp'
    temporary.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temporary,folder/'resumo.json')
    with (folder/'resumo.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['empresa','status_empresa','relatorio','arquivo','status','bytes','paginas','segundos'])
        writer.writeheader()
        for company in clean['empresas']:
            for r in company['relatorios'] or [{}]:
                writer.writerow({'empresa':company['empresa'],'status_empresa':company['status'],
                    **{k:r.get(k,'') for k in writer.fieldnames if k not in {'empresa','status_empresa'}}})


def publish(source,target):
    """Reserva exclusiva impede sobrescrita, inclusive entre volumes."""
    created=False
    try:
        with target.open('xb') as out:
            created=True
            with source.open('rb') as src: shutil.copyfileobj(src,out)
            out.flush(); os.fsync(out.fileno())
        if target.stat().st_size!=source.stat().st_size: raise OSError('copia_incompleta')
        source.unlink()
    except Exception:
        if created: target.unlink(missing_ok=True)
        raise


class Processor:
    def __init__(self,backend,emit=None,stop=None,validate_pdf=None,temporary_root=None):
        self.backend=backend; self.emit=emit or (lambda event:None)
        self.stop=stop or threading.Event(); self.validate_pdf=validate_pdf or self._pdf
        self.temporary_root=Path(temporary_root) if temporary_root else DATA/'temporarios'

    def _pdf(self,path):
        import pymupdf
        with pymupdf.open(path) as pdf:
            if pdf.needs_pass or pdf.page_count<1 or pdf.is_repaired: raise ValueError('PDF sem integridade estrutural.')
            for page in pdf: page.get_displaylist()
            return {'bytes':path.stat().st_size,'paginas':pdf.page_count}

    def run(self,jobs,competence,destination,run):
        run=Path(run); run.mkdir(parents=True,exist_ok=False)
        begin=time.monotonic(); summary={'sucesso':False,'empresas':[],'pdfs':0,'total_segundos':0}
        try:
            start,end=period(competence)
            if not jobs: raise ValueError('Selecione pelo menos uma empresa.')
            root=Path(destination).expanduser().resolve()
            if root.exists() and not root.is_dir(): raise ValueError('Destino inválido.')
            seen=set(); prepared=[]
            for i,job in enumerate(jobs,1):
                number=cnpj(job['cnpj'])
                if number in seen: raise ValueError('Empresa repetida na seleção.')
                seen.add(number)
                rows=[r for r in validate_settings(job['relatorios']) if r['selecionado']]
                rows=[{**r,'opcional':False} for r in rows]
                if not rows: raise ValueError('Empresa sem relatórios selecionados.')
                folder=root/start.strftime('%Y-%m')/folder_name(job['name'],number)
                if folder.exists() and not folder.is_dir(): raise ValueError('Pasta de empresa inválida.')
                if any((folder/r['nome_pdf']).exists() for r in rows): raise UserError('Já existem PDFs deste lote na pasta escolhida. Escolha outra pasta principal para tentar novamente sem sobrescrever arquivos.')
                criteria={'cnpj':number,'inicio':start.strftime('%d/%m/%Y'),'fim':end.strftime('%d/%m/%Y')}
                row={'empresa':f'empresa_{i:03d}','nome':redact(job['name']),'status':'Aguardando','relatorios':[
                    {'id':r['id'],'relatorio':r['caminho_pva'][-1],'arquivo':redact(r['nome_pdf']),'status':'não executado'} for r in rows]}
                summary['empresas'].append(row); prepared.append((job,rows,criteria,folder,row))
            total=sum(len(rows) for _,rows,_,_,_ in prepared); done=0
            persist(run,summary)
            identity=None
            for i,(job,rows,criteria,folder,company) in enumerate(prepared,1):
                if self.stop.is_set(): company['status']='Interrompida'; break
                state=self.backend.estado(criteria,run/f'{i:03d}_inicial')
                reuse=i==1 and correct(state)
                if not reuse and not safe_empty(state):
                    if state.get('modal_aberta'):raise UserError('Há um diálogo aberto no PVA. Conclua ou cancele essa janela manualmente e tente novamente.')
                    if state.get('aberta'):raise UserError('Há outra empresa ou competência aberta no PVA. Essa escrituração foi preservada.')
                    raise UserError('Não foi possível confirmar o estado do PVA. Verifique a janela e tente novamente.')
                if identity is None: identity=state['janela']
                if state['janela']!=identity: raise RuntimeError('Janela do PVA mudou.')
                company['status']='Processando'
                self.emit({'tipo':'empresa','indice':i-1,'status':'Processando','empresa':job['name'],
                           'concluidas':sum(c['status']=='Concluída' for c in summary['empresas']),
                           'total_empresas':len(jobs),'total':total,'feitos':done,'pdfs':summary['pdfs']})
                company['escrituracao_reutilizada']=reuse
                opened=None if reuse else self.backend.abrir(criteria,identity,run/f'{i:03d}_abertura')
                if not reuse and not (opened.get('correspondencia_unica') and opened.get('selecao_confirmada')
                        and opened.get('ok_tentativas')==1 and opened.get('identidade_aberta_confirmada')
                        and not any(opened.get(k) for k in ('erro_tipo','timeout','worker_pendente'))):
                    # So continuar para outra empresa se o PVA estiver comprovadamente vazio.
                    company['status']='Falha'; company['motivo']='Abertura não confirmada ou correspondência ausente/ambígua.'
                    reason=opened.get('motivo')
                    technical=(opened.get('erro_tipo') and reason!='correspondencia_ausente_ou_ambigua') or opened.get('timeout')
                    if technical:
                        company['motivo']=('Não foi possível ativar a janela do PVA. Verifique se ela está disponível e tente iniciar novamente.'
                            if reason=='foco_nao_confirmado' else 'Um componente do automatizador falhou antes de confirmar a abertura. Nenhuma próxima empresa será iniciada.')
                        raise UserError(company['motivo'])
                    if opened.get('worker_pendente'):raise RuntimeError('Processo auxiliar pendente; estado requer revisão.')
                    empty=self.backend.estado(criteria,run/f'{i:03d}_apos_falha')
                    if safe_empty(empty) and empty['janela']==identity:
                        done+=len(rows); self._save(run,summary,i,company)
                        self.emit({'tipo':'empresa','indice':i-1,'status':'Falha','feitos':done,'total':total,
                            'pdfs':summary['pdfs'],'concluidas':sum(c['status']=='Concluída' for c in summary['empresas']),
                            'total_empresas':len(jobs)})
                        continue
                    raise RuntimeError('Falha de abertura; estado do PVA requer revisão.')
                state=self.backend.estado(criteria,run/f'{i:03d}_confirmar')
                if not correct(state) or state['janela']!=identity: raise RuntimeError('Rodapé divergente ou ilegível.')
                folder.mkdir(parents=True,exist_ok=True)
                for j,(case,row) in enumerate(zip(rows,company['relatorios']),1):
                    if self.stop.is_set(): company['status']='Interrompida'; break
                    if list(self.backend.identificar())!=list(identity): raise RuntimeError('PVA mudou ou diálogo inesperado.')
                    self.emit({'tipo':'relatorio','indice':i-1,'empresa':job['name'],'relatorio':row['relatorio'],
                               'feitos':done,'total':total,'pdfs':summary['pdfs']})
                    stage=self.temporary_root/run.name/f'{i:03d}_{j:03d}.pdf'; stage.parent.mkdir(parents=True,exist_ok=True)
                    if (folder/case['nome_pdf']).exists() or stage.exists(): raise FileExistsError('Arquivo já existe.')
                    # Reutilizar supervisor aprovado. Logs recebem somente caminho temporario
                    # e identificadores de relatorio, nunca CNPJ da pasta de destino final.
                    safe_case={**case,'nome_pdf':case['id']+'.pdf','destino':str(stage),'exigir_marcadores':False}
                    t=time.monotonic()
                    with (run/'fluxo.stdout.txt').open('a',encoding='utf-8') as stream,contextlib.redirect_stdout(stream):
                        item=self.backend.report(safe_case,run/f'{i:03d}_{j:03d}_relatorio')
                    row['segundos']=round(time.monotonic()-t,4)
                    if not item.get('sucesso') or item.get('A_permanece_vivo'):
                        row['status']='falha'; raise RuntimeError('Relatório falhou; nenhum clique será repetido e a escrituração permanecerá aberta.')
                    if item.get('ignorado'):
                        row['status']='falha';raise RuntimeError('Relatório obrigatório indisponível.')
                    else:
                        row.update(self.validate_pdf(stage))
                        publish(stage,folder/case['nome_pdf'])
                        row['status']='gerado'; summary['pdfs']+=1
                    done+=1; self._save(run,summary,i,company)
                    self.emit({'tipo':'progresso','indice':i-1,'feitos':done,'total':total,'pdfs':summary['pdfs']})
                if self.stop.is_set(): company['status']='Interrompida'; self._save(run,summary,i,company); break
                state=self.backend.estado(criteria,run/f'{i:03d}_antes_fechar')
                if not correct(state) or state['janela']!=identity: raise RuntimeError('Identidade não confirmada antes de fechar.')
                closed=self.backend.close(criteria,run/f'{i:03d}_fechar')
                if not closed.get('sucesso') or not closed.get('fechamento_confirmado') or closed.get('erro_tipo'):
                    raise RuntimeError('Fechamento não confirmado; não iniciar próxima empresa.')
                state=self.backend.estado(criteria,run/f'{i:03d}_vazio')
                if not safe_empty(state) or state['janela']!=identity: raise RuntimeError('Escrituração permaneceu aberta.')
                company['status']='Concluída'; self._save(run,summary,i,company)
                self.emit({'tipo':'empresa','indice':i-1,'status':'Concluída',
                           'concluidas':sum(c['status']=='Concluída' for c in summary['empresas']),'total_empresas':len(jobs),
                           'feitos':done,'total':total,'pdfs':summary['pdfs']})
            summary['sucesso']=all(c['status']=='Concluída' for c in summary['empresas'])
            summary['interrompida']=self.stop.is_set()
        except Exception as exc:
            summary['erro_tipo']=type(exc).__name__
            # Mensagens de excecoes externas nunca vao para logs.
            summary['motivo']=str(exc) if isinstance(exc,UserError) else 'Processamento interrompido; verifique o PVA antes de nova execução.'
            for c in summary['empresas']:
                if c['status']=='Processando': c['status']='Falha'
            self.emit({'tipo':'mensagem','texto':summary['motivo']})
        finally:
            try:summary['auxiliares_pendentes']=getattr(self.backend,'pending_workers',lambda:[])()
            except Exception:summary['auxiliares_pendentes']=[0]
            summary['total_segundos']=round(time.monotonic()-begin,4)
            persist(run,summary)
            for i,c in enumerate(summary['empresas'],1): self._save(run,summary,i,c)
        return summary

    def _save(self,run,summary,index,company):
        persist(run,summary)
        persist(run/f'empresa_{index:03d}',{'empresas':[company]})
