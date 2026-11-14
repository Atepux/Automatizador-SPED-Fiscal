"""Coordenacao V2: uma empresa, sem fechamento automatico de escrituracao."""
from datetime import datetime
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import time
import tomllib

from execucao_runtime import RESOURCES
BASE = RESOURCES
sys.path.insert(0, str(BASE))
import geracao_v1 as geracao
from selecao_escrituracao import validate, date


class FluxoInterrompido(RuntimeError): pass


def destino_empresa(raiz, empresa, criterios):
    validate(criterios)
    if (not empresa or empresa != empresa.strip() or empresa in {'.','..'}
        or any(c in empresa for c in '<>:"/\\|?*') or empresa.endswith('.')
        or any(ord(c)<32 for c in empresa)
        or re.search(r'\d{14}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',empresa)
        or empresa.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}):
        raise ValueError('alias_empresa_invalido_nao_usar_cnpj')
    inicio, fim = date(criterios['inicio']), date(criterios['fim'])
    if inicio[:7] != fim[:7]: raise ValueError('competencia_deve_ser_mensal')
    return Path(raiz).expanduser().resolve()/empresa/inicio[:7]


def exigir_identidade(estado):
    if (estado.get('erro_tipo') or estado.get('timeout') or estado.get('modal_aberta')
        or estado.get('aberta') is not True or estado.get('rodape_lido') is not True
        or estado.get('identidade_aberta_confirmada') is not True):
        raise FluxoInterrompido('identidade_nao_confirmada_ou_outra_escrituracao')


def executar(criterios, empresa, raiz, run, backend, runner=None):
    """Backend injetavel para testes offline. Nenhuma entrada fiscal e persistida."""
    run = Path(run); run.mkdir(parents=True, exist_ok=False)
    cadastro = [{**r,'opcional':False} for r in geracao.carregar_cadastro()]
    summary = {'versao':'2.0.0-empresa-unica','sucesso':False,'relatorios':[
        {'id':c['id'],'relatorio':c['caminho_pva'][-1],'arquivo':c['nome_pdf'],
         'status':'não executado'} for c in cadastro]}
    started = time.monotonic()
    try:
        destino = destino_empresa(raiz,empresa,criterios)
        # Nao registrar alias/caminhos absolutos, que podem conter identificadores.
        geracao.verificar_arquivos_existentes(destino,cadastro)
        estado = backend.estado(criterios,run/'estado_inicial')
        if estado.get('erro_tipo') or estado.get('timeout') or estado.get('modal_aberta'):
            raise FluxoInterrompido('estado_inicial_nao_seguro')
        identity = estado.get('janela')
        if not identity: raise FluxoInterrompido('janela_nao_identificada')
        if estado.get('aberta') is True:
            exigir_identidade(estado)
            summary['escrituracao_reutilizada'] = True
        elif estado.get('aberta') is False and estado.get('pode_abrir') is True:
            opened = backend.abrir(criterios,identity,run/'abertura')
            if (opened.get('erro_tipo') or opened.get('timeout') or opened.get('worker_pendente')
                or not opened.get('correspondencia_unica') or not opened.get('selecao_confirmada')
                or opened.get('ok_tentativas') != 1 or not opened.get('identidade_aberta_confirmada')):
                raise FluxoInterrompido('abertura_nao_confirmada')
            summary['escrituracao_reutilizada'] = False
        else: raise FluxoInterrompido('estado_abertura_ambiguo')
        # Nova confirmacao imediatamente antes de entregar o controle a geracao.
        confirmado = backend.estado(criterios,run/'estado_antes_geracao')
        exigir_identidade(confirmado)
        if confirmado.get('janela') != identity:
            raise FluxoInterrompido('janela_pva_alterada')
        summary['identidade_confirmada'] = True
        destino.mkdir(parents=True,exist_ok=True)
        reports = run/'relatorios'; reports.mkdir()
        def identificar():
            observed = backend.identificar()
            if list(observed) != list(identity):
                raise FluxoInterrompido('janela_pva_alterada')
            return observed
        if runner is None:
            from poc_ponta_a_ponta import supervisor
            runner=supervisor
        def mandatory_runner(folder,case):
            item=runner(folder,{**case,'opcional':False})
            if item.get('ignorado'):
                return {**item,'sucesso':False,'ignorado':False,'erro_tipo':'RelatorioObrigatorioAusente'}
            return item
        result = geracao.executar_lote(cadastro,destino,reports,runner=mandatory_runner,identificar=identificar)
        # O resumo original aprovado e mantido em relatorios/. O resumo V2 nao
        # duplica o destino absoluto nem os criterios fiscais de identificacao.
        for field in ('sucesso','relatorios','workers_pendentes','revisao_necessaria','erro_tipo','motivo_interrupcao'):
            if field in result: summary[field] = result[field]
    except (Exception,KeyboardInterrupt) as exc:
        summary.update(sucesso=False,erro_tipo=type(exc).__name__)
        if isinstance(exc,FluxoInterrompido): summary['motivo_interrupcao'] = str(exc)
    finally:
        summary['total_segundos'] = round(time.monotonic()-started,4)
        geracao.gravar_resumo(run,summary)
    return summary


def revisao_offline():
    cadastro = geracao.carregar_cadastro()
    baseline = json.loads((BASE/'v1_preservacao.json').read_text('utf-8'))
    falhas = []
    changes_path = BASE/'config/ajustes_v2.json'
    changes = json.loads(changes_path.read_text('utf-8')) if changes_path.exists() else {}
    settings = tomllib.loads((BASE/'config/diagnostico.toml').read_text('utf-8'))
    if settings.get('espera_apos_abrir_relatorio_segundos',0) < 2:
        falhas.append('espera_apos_relatorio_menor_que_2s')
    for entry in baseline['componentes_copiados']:
        path = BASE/entry['arquivo']
        current = hashlib.sha256(path.read_bytes()).hexdigest()
        change = changes.get(entry['arquivo'],{})
        if current != entry['sha256'] and not (change.get('origem_sha256')==entry['sha256']
                and change.get('v2_sha256')==current and change.get('motivo')):
            falhas.append('componente_aprovado_modificado_sem_registro:'+entry['arquivo'])
    if geracao.BASE.resolve() != BASE.resolve(): falhas.append('geracao_fora_v2')
    for name in ('poc_ponta_a_ponta','navegacao_arvore','subrelatorios','janelas_recibo'):
        module = importlib.import_module(name)
        if not Path(module.__file__).resolve().is_relative_to(BASE): falhas.append('importacao_fora_v2:'+name)
    return {'aprovado':not falhas,'falhas':falhas,'relatorios':len(cadastro),
            'principais':8,'opcional':0,'PVA_acessado':False}
