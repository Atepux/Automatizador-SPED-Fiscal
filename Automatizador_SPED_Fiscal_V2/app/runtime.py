"""Recursos imutaveis separados dos cadastros e logs do usuario."""
import io
import os
from pathlib import Path
import sys

RESOURCES=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
DATA=(Path(os.environ.get('LOCALAPPDATA',Path.home()))/'AutomatizadorSPEDFiscal'/'V2'
      if getattr(sys,'frozen',False) else RESOURCES)
APP_VERSION='2.3.3'


def validate_resources():
    """Confere os modulos realmente importados, inclusive no EXE congelado."""
    import importlib,tomllib
    sys.path.insert(0,str(RESOURCES/'scripts'))
    settings=RESOURCES/'config/diagnostico.toml'
    config=tomllib.loads(settings.read_text('utf-8'))
    if config.get('espera_apos_abrir_relatorio_segundos',0)<2:raise ValueError('configuracao_de_espera_invalida')
    checked=[]
    for name in ('backend_empresa','modal_concorrente','diagnostico_escrituracoes','selecao_escrituracao',
                 'ativar_operacoes_proprias','concluir_pdf_fisico','testar_salvar_fisico','poc_ponta_a_ponta','empresa_unica'):
        module=importlib.import_module(name)
        root=getattr(module,'ROOT',getattr(module,'BASE',None))
        if root is None or Path(root).resolve()!=RESOURCES.resolve():raise ValueError('raiz_de_recurso_incorreta:'+name)
        if not (Path(root)/'config/diagnostico.toml').is_file():raise FileNotFoundError('configuracao_de_auxiliar_ausente')
        checked.append(name)
    return {'configuracao':True,'modulos':checked,'PVA_acessado':False}


def command(script,*args):
    relative=Path(script).as_posix()
    if getattr(sys,'frozen',False):return [sys.executable,'--sped-worker',relative,*map(str,args)]
    return [sys.executable,'-u',str(RESOURCES/'worker_entry.py'),'--sped-worker',relative,*map(str,args)]


def setup_streams():
    if os.name!='nt':return
    import ctypes,msvcrt
    for name,handle,mode,flags in [('stdin',-10,'r',os.O_RDONLY),('stdout',-11,'w',os.O_WRONLY),('stderr',-12,'w',os.O_WRONLY)]:
        if getattr(sys,name,None) is not None:continue
        native=ctypes.windll.kernel32.GetStdHandle(handle)
        try:
            if not native or native==-1:raise OSError()
            fd=msvcrt.open_osfhandle(native,flags)
            stream=io.open(fd,mode,encoding='utf-8',errors='replace',buffering=1)
        except (OSError,ValueError):stream=open(os.devnull,mode,encoding='utf-8')
        setattr(sys,name,stream)


def prepare_bridge():
    """Somente neste processo: ponte preferida e deteccao nao destrutiva."""
    from .environment import bridge_path,properties_enabled
    from pyjab.common.service import Service
    klass=Service.__wrapped__
    original=klass.find_bridge_dll
    def locate(self,bridge_dll=None):
        own=bridge_path()
        return own if own.is_file() else original(self,bridge_dll)
    klass.find_bridge_dll=locate
    klass.is_bridge_enabled=lambda self:properties_enabled()
