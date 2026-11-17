"""Distribuicao: runtime privado + iniciador unico, sem dados do usuario."""
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile

BASE=Path(__file__).resolve().parents[1]
VERSION='2.3.3'
STAMP=time.strftime('%Y%m%d_%H%M%S')
WORK=BASE/'empacotamento'/('build_'+STAMP)
RELEASE=BASE/'entrega'


def run(args):
    subprocess.run([sys.executable,'-m','PyInstaller',*args],check=True,cwd=BASE)


def zip_tree(source,target):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(source.rglob('*')):
            if file.is_file():z.write(file,file.relative_to(source).as_posix())


def main():
    WORK.mkdir(parents=True);RELEASE.mkdir(exist_ok=True)
    resources=WORK/'resources';resources.mkdir()
    (resources/'config').mkdir()
    # Somente configuracoes tecnicas e catalogo; nunca DB, logs ou PDFs.
    for path in (BASE/'config').glob('*'):
        if path.suffix in {'.json','.toml'}:shutil.copy2(path,resources/'config'/path.name)
    diagnostic=(resources/'config/diagnostico.toml').read_text('utf-8')
    diagnostic='\n'.join('bridge_dll = ""' if line.startswith('bridge_dll') else line for line in diagnostic.splitlines())+'\n'
    (resources/'config/diagnostico.toml').write_text(diagnostic,encoding='utf-8')
    (resources/'config/programa.json').write_text(json.dumps({'versao':VERSION,'python_executavel':'embutido no executavel'}),encoding='utf-8')
    (resources/'scripts').mkdir()
    for file in (BASE/'scripts').glob('*.py'):shutil.copy2(file,resources/'scripts'/file.name)
    sources=WORK/'FONTES';sources.mkdir()
    own=sources/'Automatizador_SPED_Fiscal_fontes.zip'
    with zipfile.ZipFile(own,'w',zipfile.ZIP_DEFLATED) as z:
        for folder in ('app','scripts','tests'):
            for file in (BASE/folder).glob('*.py'):z.write(file,f'{folder}/{file.name}')
        for name in ('interface.py','worker_entry.py','executar_empresa.py','geracao_v1.py','Iniciar.bat','INSTRUCOES_INTERFACE.md','GUIA_DISTRIBUICAO.md','requirements_interface.txt','LICENSE-AGPL-3.0.txt','v1_preservacao.json'):
            if (BASE/name).exists():z.write(BASE/name,name)
        for file in (resources/'config').glob('*'):z.write(file,'config/'+file.name)
        for file in (BASE/'empacotamento').glob('*.py'):z.write(file,'empacotamento/'+file.name)
        icon_source=BASE/'recursos/SPED_Minimalista.ico'
        if icon_source.is_file():z.write(icon_source,'recursos/'+icon_source.name)
    dist=metadata.distribution('PyMuPDF');copying=dist.locate_file('pymupdf-1.26.7.dist-info/COPYING')
    shutil.copy2(copying,sources/'AGPL-3.0.txt')
    # Fontes completos de compilacao dos dois componentes AGPL, sem amostras
    # PDF de teste do fornecedor que nao participam da compilacao da biblioteca.
    vendor=BASE/'empacotamento/fornecedores'
    with tarfile.open(vendor/'pymupdf-1.26.7.tar.gz') as t,zipfile.ZipFile(sources/'PyMuPDF-1.26.7-fontes.zip','w',zipfile.ZIP_DEFLATED) as z:
        for entry in t.getmembers():
            if entry.isfile() and '/tests/resources/' not in entry.name:
                z.writestr(entry.name,t.extractfile(entry).read())
    shutil.copy2(vendor/'mupdf-1.26.12-source.tar.gz',sources/'mupdf-1.26.12-source.tar.gz')
    # A instalacao local do pyjab inclui adaptacoes aprovadas: preservar os
    # fontes exatos, nao substitui-los por uma versao diferente do PyPI.
    package=Path(__import__('pyjab').__file__).parent
    with zipfile.ZipFile(sources/'pyjab-1.12.0-fontes.zip','w',zipfile.ZIP_DEFLATED) as z:
        for file in package.rglob('*.py'):z.write(file,'pyjab/'+file.relative_to(package).as_posix())
    licenses=sources/'licencas';licenses.mkdir()
    for name in ('pyjab','xlrd','pywin32','openpyxl','et_xmlfile','pyinstaller'):
        d=metadata.distribution(name)
        for file in d.files or []:
            if '..' in file.parts:continue
            if ('license' in str(file).lower() or 'copying' in str(file).lower()) and d.locate_file(file).is_file():
                target=licenses/name/str(file);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(d.locate_file(file),target)
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',licenses/'Python-LICENSE.txt')
    (sources/'LEIA-ME.txt').write_text('Aplicativo distribuído sob GNU AGPL v3, conforme autorização do titular.\n'
        'Os fontes e scripts de compilação do aplicativo estão no ZIP.\n'
        'PyMuPDF 1.26.7: https://pypi.org/project/PyMuPDF/1.26.7/\n'
        'O ZIP PyMuPDF omite apenas PDFs/imagens de regressão em tests/resources; o sdist integral está no endereço acima.\n'
        'MuPDF 1.26.12: https://mupdf.com/downloads/archive/mupdf-1.26.12-source.tar.gz\n'
        'O componente Java é baixado diretamente de Azul no primeiro preparo, não é redistribuído neste executável.\n'
        'Não há cadastro, CNPJ de cliente, escrituração ou PDF fiscal neste pacote.\n',encoding='utf-8')
    (sources/'REPRODUZIR.txt').write_text('Python 3.14 32 bits no Windows.\n'
        'pip install pyinstaller==6.22.3 PyMuPDF==1.26.7 pywin32==312 openpyxl==3.1.5 xlrd==2.0.2\n'
        'Extraia Automatizador_SPED_Fiscal_fontes.zip e pyjab-1.12.0-fontes.zip na mesma pasta.\n'
        'Fontes originais de terceiros para a pasta empacotamento/fornecedores:\n'
        'https://pypi.org/pypi/PyMuPDF/1.26.7/json (sdist pymupdf-1.26.7.tar.gz)\n'
        'https://mupdf.com/downloads/archive/mupdf-1.26.12-source.tar.gz\n'
        'Depois: python empacotamento/construir.py\n'
        'Teste: python -m unittest discover -s tests -q\n'
        'A compilação não usa dados/ logs/ saida/ nem acessa o PVA.\n',encoding='utf-8')
    icon=BASE/'recursos/SPED_Minimalista.ico'
    if not icon.is_file():raise FileNotFoundError('Icone oficial ausente: '+str(icon))
    icon_args=['--icon',str(icon)]
    icon_data=['--add-data',str(icon)+';recursos'] if icon.is_file() else []
    runtime_dist=WORK/'runtime_dist'
    args=['--noconfirm','--clean','--windowed','--onedir','--noupx','--name','SpedFiscal',
          *icon_args,*icon_data,'--distpath',str(runtime_dist),'--workpath',str(WORK/'work_app'),'--specpath',str(WORK),
          '--paths',str(BASE),'--paths',str(BASE/'scripts'),
          '--add-data',str(resources/'config')+';config','--add-data',str(resources/'scripts')+';scripts',
          '--add-data',str(BASE/'app/pva_worker.py')+';app','--add-data',str(BASE/'app/offline_worker.py')+';app',
          '--add-data',str(sources)+';FONTES','--collect-submodules','app','--collect-submodules','pyjab',
          '--collect-all','pymupdf','--collect-all','openpyxl','--collect-all','xlrd',
          '--hidden-import','win32timezone','--hidden-import','win32gui','--hidden-import','win32api',
          '--hidden-import','win32process','--hidden-import','win32event','--hidden-import','win32con',
          '--hidden-import','pythoncom','--hidden-import','win32com.client','--hidden-import','worker_entry',
          '--exclude-module','matplotlib','--exclude-module','pandas','--exclude-module','numpy',str(BASE/'interface.py')]
    run(args)
    app=runtime_dist/'SpedFiscal'
    report=WORK/'autoteste_runtime.json'
    subprocess.run([str(app/'SpedFiscal.exe'),'--autoteste',str(report)],check=True,timeout=90)
    test=json.loads(report.read_text('utf-8'))
    if not test.get('sucesso'):raise RuntimeError('Autoteste do runtime falhou: '+str(report))
    loader=WORK/'loader';loader.mkdir()
    zip_tree(app,loader/'programa.zip')
    digest=hashlib.sha256((loader/'programa.zip').read_bytes()).hexdigest()
    (loader/'pacote.json').write_text(json.dumps({'versao':VERSION,'sha256':digest}),encoding='utf-8')
    output_name='Automatizador_SPED_Fiscal_V2_'+VERSION
    run(['--noconfirm','--clean','--windowed','--onefile','--noupx','--name',output_name,
        *icon_args,'--distpath',str(RELEASE),'--workpath',str(WORK/'work_loader'),'--specpath',str(WORK),
        '--add-data',str(loader/'programa.zip')+';.','--add-data',str(loader/'pacote.json')+';.',
        str(BASE/'empacotamento/launcher.py')])
    exe=RELEASE/(output_name+'.exe')
    release_report=BASE/'logs/autoteste_executavel_final.json'
    # Autoteste em perfil limpo local, sem escrever no cadastro do usuario.
    test_profile=WORK/'perfil_teste';test_profile.mkdir()
    test_env={**os.environ,'LOCALAPPDATA':str(test_profile)}
    subprocess.run([str(exe),'--autoteste',str(release_report)],check=True,timeout=120,env=test_env)
    final=json.loads(release_report.read_text('utf-8'))
    if not final.get('sucesso'):raise RuntimeError('Autoteste final falhou.')
    shutil.copy2(BASE/'GUIA_DISTRIBUICAO.md',RELEASE/'LEIA-ME.md')
    final.update(executavel=str(exe),bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),versao=VERSION)
    (RELEASE/'VERIFICACAO.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
    (RELEASE/('VERIFICACAO_'+VERSION+'.json')).write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(final,ensure_ascii=True),flush=True)


if __name__=='__main__':main()
