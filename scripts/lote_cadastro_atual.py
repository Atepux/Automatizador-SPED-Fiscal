"""Lote autorizado do cadastro atual, sem trocar escrituracao; sem retry."""
from datetime import datetime
import json
from pathlib import Path
import time
import sys
from modal_concorrente import ROOT,state,log
from poc_ponta_a_ponta import supervisor


def main():
    import win32gui as g
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=logs/('lote_completo_'+stamp);run.mkdir()
    output=ROOT/'saida'/('TESTE_LOTE_COMPLETO_'+stamp)
    result={'sucesso':False,'pasta_saida':str(output),'relatorios':[]};started=time.monotonic()
    try:
        config=json.loads((ROOT/'config/poc_tres_relatorios.json').read_text('utf-8'))['relatorios']
        allowed={'operacoes_proprias','operacoes_st','documentos_entradas','pagamentos_eletronicos','recibo','ciap','documentos_saidas','controle_creditos_fiscais'}
        if len(config)!=8 or {c['id'] for c in config}!=allowed:raise RuntimeError('cadastro_fora_autorizacao')
        if [c['id'] for c in config if c.get('exibir_subrelatorios')]!=['operacoes_proprias','operacoes_st']:raise RuntimeError('regra_subrelatorios_invalida')
        if [c['id'] for c in config if c.get('opcional')]!=['controle_creditos_fiscais']:raise RuntimeError('opcional_invalido')
        names=[c['nome_pdf'] for c in config]
        if len(set(n.casefold() for n in names))!=8 or any(Path(n).name!=n for n in names):raise RuntimeError('nomes_invalidos')
        renewed=len(sys.argv)==2 and sys.argv[1] in {'--nova-autorizacao-ordem-atual','--autorizacao-espera-2s'}
        if renewed and [c['id'] for c in config]!=['documentos_entradas','documentos_saidas','operacoes_proprias','operacoes_st','ciap','controle_creditos_fiscais','pagamentos_eletronicos','recibo']:
            raise RuntimeError('ordem_divergente_da_autorizada')
        lock=('lote_completo_espera_2s_autorizacao.lock' if '--autorizacao-espera-2s' in sys.argv else
              'lote_completo_nova_ordem_autorizacao.lock' if renewed else 'lote_completo_autorizacao.lock')
        with (logs/lock).open('x',encoding='utf-8') as f:f.write(str(run))
        output.mkdir(parents=True,exist_ok=False)
        main,pid,_=state();result.update(pid_pva=pid,hwnd_principal=main)
        for index,case in enumerate(config,1):
            current=state()
            if current[:2]!=(main,pid) or any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in current[2]):raise RuntimeError('pva_mudou_ou_modal_aberta')
            dest=output/case['nome_pdf']
            if dest.exists():raise RuntimeError('destino_ja_existe')
            log(run/'eventos.jsonl','iniciar_relatorio',id=case['id'],indice=index)
            # Novos marcadores nao foram validados. Sao informativos; a
            # autorizacao atual exige PDF estrutural valido, nao essas heuristicas.
            item=supervisor(run/('%02d_'%index+case['id']),{**case,'destino':str(dest),'exigir_marcadores':False})
            item.update(id=case['id'],nome_pdf=case['nome_pdf'])
            item['status']=item.get('status') or ('ignorado_indisponivel' if item.get('ignorado') else 'gerado' if item['sucesso'] else 'erro')
            result['relatorios'].append(item)
            (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'relatorio':case['id'],'status':item['status']},ensure_ascii=True),flush=True)
            if not item['sucesso']:break
        completed={x['id'] for x in result['relatorios']}
        result['nao_executados']=[c['id'] for c in config if c['id'] not in completed]
        result['sucesso']=len(completed)==8 and all(x['sucesso'] for x in result['relatorios'])
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        log(run/'eventos.jsonl','erro_lote',tipo=type(exc).__name__)
    finally:
        result['total_segundos']=round(time.monotonic()-started,4)
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),'sucesso':result['sucesso'],'pasta_saida':str(output),
                          'total_segundos':result['total_segundos'],'executados':len(result['relatorios'])},ensure_ascii=True),flush=True)


if __name__=='__main__':main()
