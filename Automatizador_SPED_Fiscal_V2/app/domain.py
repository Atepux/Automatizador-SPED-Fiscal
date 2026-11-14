import calendar
from datetime import date
import re
import unicodedata

DEFAULTS = {'documentos_entradas','documentos_saidas','operacoes_proprias','operacoes_st','recibo'}
ORDER = ['documentos_entradas','documentos_saidas','operacoes_proprias','operacoes_st','ciap',
         'controle_creditos_fiscais','pagamentos_eletronicos','recibo']


def format_competence(value,deleting=False):
    digits=re.sub(r'\D','',value)[:6]
    if len(digits)>2:return digits[:2]+'/'+digits[2:]
    return digits+('/' if len(digits)==2 and not deleting else '')


def cnpj(value):
    if not isinstance(value,str) or not re.fullmatch(r'[\d./\-\s]+',value):
        raise ValueError('CNPJ deve conter 14 dígitos, com ou sem pontuação.')
    number = re.sub(r'\D','',value)
    if len(number)!=14 or len(set(number))==1: raise ValueError('CNPJ inválido.')
    for length,weights in [(12,[5,4,3,2,9,8,7,6,5,4,3,2]),(13,[6,5,4,3,2,9,8,7,6,5,4,3,2])]:
        remainder=sum(int(n)*w for n,w in zip(number[:length],weights))%11
        if int(number[length]) != (0 if remainder<2 else 11-remainder):
            raise ValueError('Dígitos verificadores do CNPJ inválidos.')
    return number


def period(value):
    if not re.fullmatch(r'\d{2}/\d{4}',value): raise ValueError('Competência: use MM/AAAA.')
    month,year=map(int,value.split('/'))
    if not 1<=month<=12 or not 1900<=year<=9999: raise ValueError('Competência inválida.')
    return date(year,month,1),date(year,month,calendar.monthrange(year,month)[1])


def filename(value):
    if (not isinstance(value,str) or not value.lower().endswith('.pdf') or value!=value.strip()
        or any(c in value for c in '<>:"/\\|?*') or any(ord(c)<32 for c in value)
        or len(value)>220 or value[:-4].strip(' .')==''
        or value.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}):
        raise ValueError('Nome PDF inválido para Windows.')
    return value


def folder_name(name,number):
    safe=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',unicodedata.normalize('NFC',name)).strip(' .')[:90]
    if not safe: safe='Empresa'
    # CNPJ evita colisão entre nomes iguais. Só o destino e o cadastro o contêm.
    return safe+' - '+cnpj(number)


def redact(value):
    if isinstance(value,dict): return {k:redact(v) for k,v in value.items()}
    if isinstance(value,list): return [redact(v) for v in value]
    if isinstance(value,str):
        return re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|(?<!\d)\d{14}(?!\d)','[CNPJ omitido]',value)
    return value


def excluded(path):
    text=' '.join(path).casefold()
    return 'difal' in text or 'diferencial de al' in text


def validate_settings(rows):
    names=set()
    for row in rows:
        filename(row['nome_pdf'])
        if not row['selecionado']: continue
        if excluded(row['caminho_pva']) or row.get('suporte')=='especial_nao_suportado':
            raise ValueError('Relatório excluído ou interação especial não suportada.')
        key=unicodedata.normalize('NFC',row['nome_pdf']).casefold()
        if key in names: raise ValueError('Nomes PDF duplicados nos relatórios selecionados.')
        names.add(key)
    return sorted(rows,key=lambda r:(ORDER.index(r['id']) if r['id'] in ORDER else len(ORDER),r['caminho_pva']))
