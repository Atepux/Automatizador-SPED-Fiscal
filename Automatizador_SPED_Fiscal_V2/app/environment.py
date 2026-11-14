"""Preparacao local do cliente JAB; nunca substitui o runtime do PVA."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import urllib.request
import zipfile
from .runtime import DATA,RESOURCES

AZUL_URL='https://cdn.azul.com/zulu/bin/zulu8.98.0.111-ca-jre8.0.512-win_i686.zip'
AZUL_SHA=''


def bridge_path():
    return DATA/'java'/'WindowsAccessBridge-32.dll'


def properties_enabled(path=None):
    path=Path(path) if path else Path.home()/'.accessibility.properties'
    if not path.exists():return False
    for line in path.read_text('latin-1').splitlines():
        if line.strip().startswith('assistive_technologies='):
            return 'com.sun.java.accessibility.AccessBridge' in [v.strip() for v in line.split('=',1)[1].split(',')]
    return False


def enable_properties(path=None):
    path=Path(path) if path else Path.home()/'.accessibility.properties'
    data=path.read_text('latin-1') if path.exists() else ''
    if properties_enabled(path):return False
    if path.exists():
        backup=path.with_name(path.name+'.sped-backup')
        if not backup.exists():shutil.copy2(path,backup)
    lines=data.splitlines();found=False
    for i,line in enumerate(lines):
        if line.strip().startswith('assistive_technologies='):
            value=line.split('=',1)[1].strip()
            lines[i]='assistive_technologies='+value+(',' if value else '')+'com.sun.java.accessibility.AccessBridge'
            found=True
    if not found:lines.append('assistive_technologies=com.sun.java.accessibility.AccessBridge')
    temp=path.with_name(path.name+'.sped-tmp')
    temp.write_text('\n'.join(lines)+'\n',encoding='latin-1');os.replace(temp,path)
    return True


def check():
    own=bridge_path()
    available=own.is_file()
    if not available:
        try:
            from pyjab.config import find_bridge_dll
            available=find_bridge_dll() is not None
        except Exception:available=False
    return {'ponte_portatil':own.is_file(),'ponte_encontrada':available,'acesso_habilitado':properties_enabled(),
            'pronto':available and properties_enabled()}


def prepare(progress=None):
    """Usuario aciona explicitamente Preparar acesso; sem instalacao global."""
    progress=progress or (lambda value:None)
    own=bridge_path();own.parent.mkdir(parents=True,exist_ok=True)
    if not own.is_file():
        metadata=json.loads((RESOURCES/'config/java_portatil.json').read_text('utf-8'))
        archive=own.parent/'download.zip.part';digest=hashlib.sha256()
        try:
            progress('Baixando componente oficial de acesso ao PVA…')
            with urllib.request.urlopen(metadata['download_url'],timeout=60) as src,archive.open('wb') as dst:
                while data:=src.read(1024*1024):dst.write(data);digest.update(data)
            if digest.hexdigest()!=metadata['sha256_hash']:raise ValueError('A verificação do download falhou. Tente novamente.')
            with zipfile.ZipFile(archive) as z:
                for suffix in ('bin/WindowsAccessBridge-32.dll','LICENSE','DISCLAIMER'):
                    match=[n for n in z.namelist() if n.endswith('/'+suffix)]
                    if len(match)!=1:raise ValueError('O pacote oficial não contém o componente esperado.')
                    blob=z.read(match[0])
                    if suffix.endswith('.dll'):
                        offset=struct.unpack_from('<I',blob,0x3c)[0]
                        if struct.unpack_from('<H',blob,offset+4)[0]!=0x14c:raise ValueError('Arquitetura da ponte incompatível.')
                    (own.parent/Path(suffix).name).write_bytes(blob)
        finally:archive.unlink(missing_ok=True)
    changed=enable_properties()
    return {'sucesso':True,'reiniciar_pva':changed,'texto':
        'Acesso preparado. Feche e abra o PVA uma vez para ativar a comunicação.' if changed else 'Acesso ao PVA já está preparado.'}
