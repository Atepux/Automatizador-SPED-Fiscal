"""Entrada V2 etapa 1: diagnostico somente de leitura; geracao desabilitada."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parent


def main():
    folder=BASE/'logs'/('diagnostico_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    folder.mkdir(parents=True,exist_ok=False)
    output=folder/'interface.json'
    with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
        p=subprocess.Popen([sys.executable,'-u',str(BASE/'scripts/diagnostico_escrituracoes.py'),str(output)],
                           stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        timeout=False
        try:p.wait(timeout=25)
        except subprocess.TimeoutExpired:
            timeout=True;p.kill();p.wait(timeout=5)  # Apenas o filho criado, nunca o PVA.
    result={'modo':'diagnostico_somente_leitura','timeout':timeout,'exit_code':p.returncode,
            'arquivo':str(output),'geracao_habilitada':False,'selecao_habilitada':False}
    if output.exists():
        data=json.loads(output.read_text('utf-8'))
        result.update(conexao_java=data.get('conexao_java',False),controles=len(data.get('controles',[])))
    (folder/'resumo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))
    return 1 if timeout or p.returncode or not result.get('conexao_java') else 0


if __name__=='__main__':sys.exit(main())
