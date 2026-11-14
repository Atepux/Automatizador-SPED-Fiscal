"""Entrada de uma empresa. Sem --executar, faz apenas revisao offline."""
import argparse
from datetime import datetime
from getpass import getpass
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

BASE = Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'scripts'))
from empresa_unica import executar,revisao_offline


def main():
    parser = argparse.ArgumentParser(description='V2 — uma empresa e uma competência')
    parser.add_argument('--executar',action='store_true')
    parser.add_argument('--verificar',action='store_true')
    parser.add_argument('--empresa',help='Alias da pasta da empresa, sem CNPJ')
    parser.add_argument('--destino-base',type=Path)
    parser.add_argument('--criterios-stdin',action='store_true',help='Criterios JSON pela entrada padrao, sem arquivo')
    args = parser.parse_args()
    check = revisao_offline()
    if args.verificar or not args.executar:
        print(json.dumps(check,ensure_ascii=False,indent=2)); return 0 if check['aprovado'] else 1
    if not check['aprovado']: return 1
    if not args.empresa or args.destino_base is None:
        parser.error('--executar exige --empresa e --destino-base')
    if args.criterios_stdin:
        criteria = json.load(sys.stdin)
    else:
        criteria = {'cnpj':getpass('CNPJ (entrada oculta): '),'inicio':input('Data inicial dd/mm/aaaa: '),
                    'fim':input('Data final dd/mm/aaaa: ')}
        for field,label in [('ie','Inscricao Estadual'),('finalidade','Finalidade do Arquivo'),('estado','Estado')]:
            value = getpass(label+' (opcional; Enter omite): ')
            if value: criteria[field] = value
    logs = BASE/'logs'; logs.mkdir(exist_ok=True)
    lock = logs/'empresa_unica_ativa.lock'
    # Bloquear tambem se uma geracao copiada V1 estiver pendente.
    if lock.exists() or (logs/'execucao_ativa.lock').exists() or (logs/'multiempresas_ativa.lock').exists(): raise RuntimeError('geracao_pendente')
    common=logs/'automacao_ativa.lock'
    with common.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid()},f)
    with lock.open('x',encoding='utf-8') as f: json.dump({'pid':os.getpid()},f)
    summary = None
    try:
        from backend_empresa import BackendJava
        run = logs/('empresa_unica_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid4().hex[:6])
        summary = executar(criteria,args.empresa,args.destino_base,run,BackendJava())
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0 if summary['sucesso'] else 1
    finally:
        # Interrupcao conserva trava para revisao manual, sem retentar acoes.
        if summary and summary.get('sucesso'):
            lock.unlink();common.unlink(missing_ok=True)


if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc:
        print(json.dumps({'sucesso':False,'erro_tipo':type(exc).__name__})); sys.exit(1)
