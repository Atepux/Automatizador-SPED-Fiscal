"""V1 mensal: escrituração escolhida manualmente; nenhum acesso no modo offline."""
import argparse
import contextlib
import csv
from datetime import datetime,timezone
import importlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import time
import tomllib
from uuid import uuid4

BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'scripts'))
ORDEM=['documentos_entradas','documentos_saidas','operacoes_proprias','operacoes_st',
       'ciap','controle_creditos_fiscais','pagamentos_eletronicos','recibo']


class ConfiguracaoInvalida(ValueError):pass


def carregar_cadastro(base=BASE):
    rows=json.loads((base/'config/relatorios.json').read_text('utf-8'))['relatorios']
    if [r.get('id') for r in rows]!=ORDEM:raise ConfiguracaoInvalida('Ordem ou IDs do cadastro divergentes.')
    seen=set()
    for r in rows:
        name=r.get('nome_pdf')
        if (not isinstance(name,str) or not name.endswith('.pdf') or name!=name.strip()
            or any(c in name for c in '<>:"/\\|?*') or any(ord(c)<32 for c in name)
            or name.casefold() in seen):raise ConfiguracaoInvalida('Nome PDF inválido ou repetido no cadastro.')
        seen.add(name.casefold())
        path=r.get('caminho_pva')
        if not isinstance(path,list) or len(path)<2 or path[0]!='Escrituração Fiscal' or not all(isinstance(s,str) and s.strip() for s in path):
            raise ConfiguracaoInvalida('Caminho hierárquico inválido.')
        if any('difal' in s.casefold() or 'diferencial de al' in s.casefold() for s in path):
            raise ConfiguracaoInvalida('DIFAL está excluído.')
        if r.get('exibir_subrelatorios') is not (r['id'] in {'operacoes_proprias','operacoes_st'}):
            raise ConfiguracaoInvalida('Regra de subrelatórios divergente.')
        if bool(r.get('opcional'))!=(r['id']=='controle_creditos_fiscais'):
            raise ConfiguracaoInvalida('Somente Controle de Créditos Fiscais é opcional.')
        if r.get('habilitado',True) is not True:raise ConfiguracaoInvalida('Item desabilitado no cadastro V1.')
    if rows[-1].get('timeout_abertura_segundos')!=5:raise ConfiguracaoInvalida('Recibo deve aguardar até 5 segundos.')
    return rows


def verificar_arquivos_existentes(destino,cadastro):
    existing=[r['nome_pdf'] for r in cadastro if (destino/r['nome_pdf']).exists()]
    if existing:raise FileExistsError('Destino contém arquivos do lote; escolha outra pasta.\n'+'\n'.join(existing))
    if destino.exists() and not destino.is_dir():raise NotADirectoryError('Destino não é uma pasta.')


def revisao_offline(base=BASE):
    cadastro=carregar_cadastro(base)
    program=json.loads((base/'config/programa.json').read_text('utf-8'))
    settings=tomllib.loads((base/'config/diagnostico.toml').read_text('utf-8'))
    bridge=Path(settings['bridge_dll'])
    issues=[]
    if not Path(program['python_executavel']).is_file():issues.append('Python configurado não encontrado.')
    if not bridge.is_file():issues.append('DLL Java Access Bridge não encontrada.')
    else:
        with bridge.open('rb') as f:
            f.seek(0x3c);offset=struct.unpack('<I',f.read(4))[0];f.seek(offset+4)
            machine=struct.unpack('<H',f.read(2))[0]
        if {0x14c:32,0x8664:64}.get(machine)!=struct.calcsize('P')*8:issues.append('Python e DLL têm arquiteturas diferentes.')
    if settings.get('espera_apos_abrir_relatorio_segundos',0)<2:issues.append('Espera de relatório menor que 2 segundos.')
    if sys.version_info<(3,11):issues.append('É necessário Python 3.11 ou posterior.')
    modules=['pyjab','win32gui','win32process','pymupdf']
    for name in modules:
        if importlib.util.find_spec(name) is None:issues.append('Biblioteca ausente: '+name)
    manifest=json.loads((base/'rotinas_aprovadas.json').read_text('utf-8'))
    import hashlib
    checked=[]
    for entry in manifest['rotinas']:
        path=base/'scripts'/entry['arquivo']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            issues.append('Rotina aprovada modificada: '+entry['arquivo'])
        module=importlib.import_module(path.stem)  # Sem chamada de interface.
        if not Path(module.__file__).resolve().is_relative_to(base.resolve()):issues.append('Importação fora da V1: '+path.stem)
        checked.append(path.name)
    return {'versao':program['versao'],'aprovado':not issues,'relatorios':len(cadastro),
            'principais':7,'opcionais':1,'rotinas_independentes':checked,'python':sys.executable,
            'python_bits':struct.calcsize('P')*8,'falhas':issues,'PVA_acessado':False}


def identificar_pva():
    from modal_concorrente import state
    import win32gui as g
    main,pid,owned=state()
    if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in owned):
        raise RuntimeError('Feche manualmente os diálogos do PVA antes de iniciar.')
    return main,pid


def escolher_destino(explicito,config):
    value=explicito or config.get('destino_padrao','')
    if not value:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk();root.withdraw()
            try:value=filedialog.askdirectory(title='Pasta dos PDFs — empresa e competência abertas no PVA',mustexist=False)
            finally:root.destroy()
        except Exception:
            value=input('Pasta de destino dos PDFs (vazio cancela): ').strip().strip('"')
    if not value:return None
    path=Path(value).expanduser()
    return (path if path.is_absolute() else BASE/path).resolve()


def gravar_resumo(run,summary):
    summary['atualizado_utc']=datetime.now(timezone.utc).isoformat()
    with (run/'resumo.json').open('w',encoding='utf-8') as f:
        json.dump(summary,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    with (run/'resumo.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['relatorio','arquivo','status','bytes','paginas','segundos'])
        writer.writeheader()
        for row in summary['relatorios']:
            writer.writerow({k:row.get(k,'') for k in writer.fieldnames})


def executar_lote(cadastro,destino,run,runner=None,identificar=None):
    if runner is None:
        from poc_ponta_a_ponta import supervisor
        runner=supervisor
    identificar=identificar or identificar_pva
    verificar_arquivos_existentes(destino,cadastro)  # Antes de qualquer ação.
    identity=identificar()
    destino.mkdir(parents=True,exist_ok=True)
    summary={'versao':'1.0.0','destino':str(destino),'sucesso':False,'relatorios':[],'workers_pendentes':False}
    started=time.monotonic()
    for case in cadastro:
        summary['relatorios'].append({'id':case['id'],'relatorio':case['caminho_pva'][-1],
                                     'arquivo':case['nome_pdf'],'status':'não executado'})
    gravar_resumo(run,summary)
    uncertain=False
    try:
        for index,(case,row) in enumerate(zip(cadastro,summary['relatorios']),1):
            if identificar()!=identity:raise RuntimeError('A janela/processo do PVA mudou. Lote interrompido.')
            print(f"[{index}/8] {row['relatorio']}...",flush=True)
            uncertain=True
            with (run/'fluxo.stdout.jsonl').open('a',encoding='utf-8') as stream,contextlib.redirect_stdout(stream):
                item=runner(run/(f'{index:02d}_'+case['id']),{**case,'destino':str(destino/case['nome_pdf']),
                                                           'exigir_marcadores':False})
            uncertain=False
            summary['workers_pendentes'] |= bool(item.get('A_permanece_vivo'))
            pdf=item.get('pdf') or {}
            row.update(status='ignorado — indisponível' if item.get('ignorado') else 'gerado' if item.get('sucesso') else item.get('status','falha'),
                       bytes=pdf.get('tamanho_bytes',''),paginas=pdf.get('paginas',''),segundos=item.get('total_segundos',''))
            if not item.get('sucesso'):
                row['erro_tipo']=item.get('erro_tipo','FalhaDeExecucao')
                summary['motivo_interrupcao']=case['id'];break
            if summary['workers_pendentes']:raise RuntimeError('Worker não finalizou; revisão necessária antes de prosseguir.')
            gravar_resumo(run,summary)
        summary['sucesso']=all(r['status'] in {'gerado','ignorado — indisponível'} for r in summary['relatorios'])
    except (Exception,KeyboardInterrupt) as exc:
        summary['erro_tipo']=type(exc).__name__
        summary['revisao_necessaria']=uncertain
    finally:
        summary.update(total_segundos=round(time.monotonic()-started,4),pid_pva=identity[1],hwnd_principal=identity[0])
        gravar_resumo(run,summary)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description='Automatizador SPED Fiscal V1 — escrituração aberta manualmente.')
    parser.add_argument('--destino',help='Pasta escolhida para os PDFs; prevalece sobre a configuração.')
    parser.add_argument('--verificar',action='store_true',help='Revisão offline, sem acessar PVA ou gerar PDFs.')
    args=parser.parse_args(argv)
    check=revisao_offline()
    if args.verificar:
        folder=BASE/'logs';folder.mkdir(exist_ok=True)
        (folder/'revisao_offline.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(check,ensure_ascii=False,indent=2));return 0 if check['aprovado'] else 1
    if not check['aprovado']:
        print('Configuração inválida:\n'+'\n'.join(check['falhas']));return 1
    cadastro=carregar_cadastro()
    # Somente identifica a janela; nunca escolhe empresa ou competência.
    identificar_pva()
    config=json.loads((BASE/'config/programa.json').read_text('utf-8'))
    destino=escolher_destino(args.destino,config)
    if destino is None:print('Cancelado. Nenhum relatório executado.');return 0
    verificar_arquivos_existentes(destino,cadastro)
    logs=BASE/'logs';logs.mkdir(exist_ok=True)
    lock=logs/'execucao_ativa.lock'
    try:
        with lock.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'inicio_utc':datetime.now(timezone.utc).isoformat()},f)
    except FileExistsError:
        print('Existe execução ativa ou pendente de revisão. Consulte logs/execucao_ativa.lock.');return 1
    run=logs/('execucao_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid4().hex[:6]);run.mkdir()
    summary=None
    try:
        summary=executar_lote(cadastro,destino,run)
        print('\nRelatório | Status | Bytes | Páginas')
        for r in summary['relatorios']:print(f"{r['relatorio']} | {r['status']} | {r.get('bytes','—')} | {r.get('paginas','—')}")
        print(f"\nTempo total: {summary['total_segundos']:.2f} s\nResumo: {run/'resumo.csv'}")
        return 0 if summary['sucesso'] else 1
    finally:
        if summary is not None and not summary.get('workers_pendentes') and not summary.get('revisao_necessaria'):
            lock.unlink()
        else:print('Trava preservada para revisão; nenhum processo do PVA será encerrado.')


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print(f'Não iniciado/interrompido: {type(exc).__name__}: {exc}')
        sys.exit(1)
