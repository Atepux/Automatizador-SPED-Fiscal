"""Sequencia fixa de tres relatorios autorizados; para na primeira falha."""
from datetime import datetime
import json
from pathlib import Path
import time
from modal_concorrente import ROOT,state,log
from poc_ponta_a_ponta import supervisor


def main():
    import win32gui as g
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    run=logs/('sequencia_tres_'+stamp);run.mkdir()
    output=ROOT/'saida'/('TESTE_TRES_RELATORIOS_'+stamp)
    result={'sucesso':False,'pasta_saida':str(output),'relatorios':[]}
    started=time.monotonic()
    try:
        with (logs/'sequencia_tres_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
        catalog=json.loads((ROOT/'config/poc_tres_relatorios.json').read_text('utf-8'))['relatorios']
        # Este script e a POC historica de tres itens, nao o lote do cadastro.
        cases=[next(c for c in catalog if c['id']==id) for id in
               ['operacoes_proprias','operacoes_st','documentos_entradas']]
        if len(cases)!=3:raise RuntimeError('exigidos_exatamente_tres')
        mandatory={'operacoes_proprias','operacoes_st'}
        if {c['id'] for c in cases}!={'operacoes_proprias','operacoes_st','documentos_entradas'}:raise RuntimeError('relatorios_fora_do_escopo_autorizado')
        if any(c.get('exibir_subrelatorios')!=(c['id'] in mandatory) for c in cases):raise RuntimeError('regra_obrigatoria_subrelatorios_invalida')
        names=[c['nome_pdf'] for c in cases]
        if len(set(n.casefold() for n in names))!=3 or any(Path(n).name!=n or not n.endswith('.pdf') for n in names):raise RuntimeError('nomes_invalidos')
        output.mkdir(parents=True,exist_ok=False)
        main_hwnd,pid,_=state()
        result.update(pid_pva=pid,hwnd_principal=main_hwnd)
        for index,case in enumerate(cases,1):
            current=state()
            if current[:2]!=(main_hwnd,pid) or any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in current[2]):
                raise RuntimeError('pva_mudou_ou_modal_aberta')
            dest=output/case['nome_pdf']
            if dest.exists():raise RuntimeError('destino_ja_existe')
            prepared={**case,'destino':str(dest)}
            log(run/'eventos.jsonl','iniciar_relatorio',id=case['id'],indice=index)
            item=supervisor(run/('%02d_'%index+case['id']),prepared)
            result['relatorios'].append({'id':case['id'],'nome_pdf':case['nome_pdf'],**item})
            (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            if not item['sucesso']:
                result['interrompido_no_relatorio']=case['id']
                break
            # O fechamento do dialogo e validado tambem pelo worker e supervisor.
            if any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in state()[2]):raise RuntimeError('modal_permanece_aberta')
        result['sucesso']=len(result['relatorios'])==3 and all(x['sucesso'] for x in result['relatorios'])
    except Exception as exc:
        result['erro_tipo']=type(exc).__name__
        log(run/'eventos.jsonl','interromper_sequencia',tipo=type(exc).__name__)
    finally:
        result['total_segundos']=round(time.monotonic()-started,4)
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':main()
