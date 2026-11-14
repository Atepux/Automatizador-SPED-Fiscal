import csv
from io import StringIO
from pathlib import Path
from .domain import cnpj

HELP = '''LAYOUT PARA IMPORTAÇÃO

Formatos aceitos: CSV, XLS e XLSM.

Coluna A: CNPJ
Coluna B: Nome da empresa

Não utilizar cabeçalho.

A primeira linha deve conter a primeira empresa.

Os CNPJs podem estar com ou sem pontuação.

Empresas já cadastradas não serão duplicadas.

Todas as empresas novas receberão automaticamente os relatórios padrão.'''


def numeric_cnpj(value,format_code=''):
    if isinstance(value,bool): raise ValueError('CNPJ numérico inválido.')
    if isinstance(value,(int,float)):
        if not float(value).is_integer() or value<0 or value>=10**14: raise ValueError('CNPJ numérico fora do formato seguro.')
        text=str(int(value))
        if len(text)==14: return text
        # Só repor zeros quando a máscara EXPLICITAMENTE preserva 14 posições.
        plain=format_code.split(';')[0].replace('\\','').replace('"','')
        if plain.count('0')==14 and not any(c in plain for c in '#Ee%'):
            return text.zfill(14)
        raise ValueError('CNPJ numérico com menos de 14 dígitos e sem máscara segura; use texto.')
    if not isinstance(value,str): raise ValueError('CNPJ vazio ou tipo inválido.')
    return value.strip()


def rows(path):
    path=Path(path); extension=path.suffix.lower()
    if extension=='.csv':
        raw=path.read_bytes()
        try: text=raw.decode('utf-8-sig')
        except UnicodeDecodeError: text=raw.decode('cp1252')
        try:
            dialect=csv.Sniffer().sniff(text[:8192],delimiters=';,\t')
            reader=csv.reader(StringIO(text,newline=''),dialect,strict=True)
        except csv.Error:
            reader=csv.reader(StringIO(text,newline=''),delimiter=';',strict=True)
        for number,row in enumerate(reader,1):
            yield number,(row[0] if row else ''),(row[1] if len(row)>1 else ''),''
    elif extension=='.xlsm':
        import openpyxl
        book=openpyxl.load_workbook(path,read_only=True,data_only=True,keep_links=False)
        try:
            for number,row in enumerate(book.worksheets[0].iter_rows(min_col=1,max_col=2),1):
                a,b=row
                yield number,a.value,b.value,a.number_format or ''
        finally: book.close()
    elif extension=='.xls':
        import xlrd
        book=xlrd.open_workbook(path,formatting_info=True,on_demand=True)
        try:
            sheet=book.sheet_by_index(0)
            for i in range(sheet.nrows):
                if not sheet.ncols: continue
                a=sheet.cell(i,0); b=sheet.cell_value(i,1) if sheet.ncols>1 else ''
                if a.ctype in (xlrd.XL_CELL_DATE,xlrd.XL_CELL_BOOLEAN,xlrd.XL_CELL_ERROR):
                    yield i+1,None,b,''; continue
                fmt=book.format_map[book.xf_list[a.xf_index].format_key].format_str
                yield i+1,a.value,b,fmt
        finally: book.release_resources()
    else: raise ValueError('Selecione CSV, XLS ou XLSM.')


def import_companies(path,store):
    result={'importadas':0,'existentes':0,'rejeitadas':0,'rejeicoes':[]}
    try:
        for line,number,name,fmt in rows(path):
            if (number is None or str(number).strip()=='') and (name is None or str(name).strip()==''): continue
            try:
                normalized=cnpj(numeric_cnpj(number,fmt))
                if not isinstance(name,str) or not name.strip(): raise ValueError('Nome da empresa vazio ou inválido.')
                if store.add(normalized,name): result['importadas']+=1
                else: result['existentes']+=1
            except ValueError as exc:
                result['rejeitadas']+=1; result['rejeicoes'].append({'linha':line,'motivo':str(exc)})
    except ImportError:
        result['erro_arquivo']='Biblioteca de leitura ausente. Instale openpyxl e xlrd no Python configurado.'
    except Exception:
        result['erro_arquivo']='Arquivo inválido, ilegível ou formato incompatível. As linhas já importadas foram preservadas.'
    return result
