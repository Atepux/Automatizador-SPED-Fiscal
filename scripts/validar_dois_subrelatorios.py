"""Dois relatorios somente, com checkbox confirmado antes da exportacao."""
from datetime import datetime
import json
from pathlib import Path
import time
import unicodedata
import sys
from modal_concorrente import ROOT,state,critical
from poc_ponta_a_ponta import supervisor


def compare(old,new):
    import pymupdf
    def read(path):
        with pymupdf.open(path) as doc:
            text=' '.join(''.join(c for c in unicodedata.normalize('NFKD',' '.join(p.get_text() for p in doc).casefold()) if not unicodedata.combining(c)).split())
            return {'bytes':path.stat().st_size,'paginas':doc.page_count},text
    a,ta=read(old);b,tb=read(new)
    fixed=['subrelatorio','detalhamento','ajustes da apuracao','obrigacoes do icms a recolher']
    new_markers={m:(m in tb and m not in ta) for m in fixed}
    return {'anterior':a,'atual':b,'texto_normalizado_igual':ta==tb,
            'marcadores_adicionais':new_markers,
            'conteudo_adicional_identificavel':any(new_markers.values()),
            'limite':'Tamanho/paginas nao provam inclusao; marcadores genericos sao indicios, nao validacao fiscal.'}


def main():
    import win32gui as g
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    run=logs/('validar_subrelatorios_'+stamp);run.mkdir()
    output=ROOT/'saida'/('TESTE_SUBRELATORIOS_'+stamp)
    result={'sucesso':False,'pasta_saida':str(output),'relatorios':[]};started=time.monotonic()
    try:
        renewed=len(sys.argv)==2 and sys.argv[1]=='--autorizacao-apos-navegacao'
        simplified=len(sys.argv)==2 and sys.argv[1]=='--autorizacao-regra-simples'
        lock='validar_subrelatorios_regra_simples.lock' if simplified else ('validar_subrelatorios_pos_navegacao.lock' if renewed else 'validar_dois_subrelatorios_autorizacao.lock')
        with (logs/lock).open('x',encoding='utf-8') as f:f.write(str(run))
        result['autorizacao_apos_navegacao']=renewed
        config=json.loads((ROOT/'config/poc_tres_relatorios.json').read_text('utf-8'))['relatorios']
        cases=[next(c for c in config if c['id']==id) for id in ['operacoes_proprias','operacoes_st']]
        if not all(c.get('exibir_subrelatorios') is True for c in cases):raise RuntimeError('regra_invalida')
        main,pid,_=state();output.mkdir(parents=True,exist_ok=False)
        for index,case in enumerate(cases,1):
            current=state()
            if current[:2]!=(main,pid) or any(g.GetClassName(h) in {'SunAwtDialog','#32770'} for h in current[2]):raise RuntimeError('pva_mudou_ou_modal')
            dest=output/case['nome_pdf'];old=ROOT/'saida/TESTE_TRES_RELATORIOS_20261113_115502'/case['nome_pdf']
            if dest.exists() or not old.is_file():raise RuntimeError('destino_existe_ou_comparacao_indisponivel')
            folder=run/('%02d_'%index+case['id'])
            item=supervisor(folder,{**case,'destino':str(dest)})
            item['id']=case['id'];result['relatorios'].append(item)
            if not item['sucesso']:break
            ar=json.loads((folder/'relatorio/resultado.json').read_text('utf-8'))
            sr=json.loads((folder/'abrir_salvar/A.resultado.json').read_text('utf-8'))
            item['subrelatorios']=ar.get('subrelatorios') or {}
            item['navegacao_pais']=ar.get('navegacao_pais',[])
            item['confirmacao_antes_exportacao']=sr.get('subrelatorios_antes_abrir_salvar') or {}
            if not item.get('subrelatorios',{}).get('final') or not item.get('confirmacao_antes_exportacao',{}).get('final'):
                item['sucesso']=False;break
            item['comparacao']=critical(run/'comparacao.eventos.jsonl','comparar_'+case['id'],lambda:compare(old,dest))
            (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        result['sucesso']=len(result['relatorios'])==2 and all(i['sucesso'] for i in result['relatorios'])
    except Exception as exc:result['erro_tipo']=type(exc).__name__
    finally:
        result['total_segundos']=round(time.monotonic()-started,4)
        (run/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':main()
