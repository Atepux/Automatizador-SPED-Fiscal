"""POC exclusiva de navegacao/abertura; nao salva nem aciona Salvar."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from modal_concorrente import ROOT


def main():
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    run=logs/('navegacao_auto_'+datetime.now().strftime('%Y%m%d_%H%M%S'));run.mkdir()
    with (logs/'navegacao_auto_autorizacao.lock').open('x',encoding='utf-8') as f:f.write(str(run))
    with (run/'stdout.txt').open('w') as out,(run/'stderr.txt').open('w') as err:
        p=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',str(run)],stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        timeout=False
        try:p.wait(timeout=30)
        except subprocess.TimeoutExpired:timeout=True
    result=json.loads((run/'resultado.json').read_text('utf-8')) if (run/'resultado.json').exists() else {}
    result.update(timeout_externo=timeout,pid_worker=p.pid,worker_preservado=timeout,exit_code=p.poll())
    (run/'resumo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'logs':str(run),**result},ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        run=Path(sys.argv[2])
        from ativar_operacoes_proprias import worker
        worker('click',run/'resultado.json',lock_path=run/'relatorio_clique.lock',auto_expand=True)
    else:main()
