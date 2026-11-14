from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from app.catalog import load_catalog,discovered
from app.domain import cnpj,period,filename,folder_name,redact,DEFAULTS,validate_settings,format_competence
from app.storage import Store
from app.importers import import_companies,numeric_cnpj,rows,HELP
from app.processing import Processor,publish


def number(base):
    text=base
    for weights in ([5,4,3,2,9,8,7,6,5,4,3,2],[6,5,4,3,2,9,8,7,6,5,4,3,2]):
        rem=sum(int(n)*w for n,w in zip(text,weights))%11;text+=str(0 if rem<2 else 11-rem)
    return text


A=number('001234560001');B=number('112345670001')


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'db.sqlite3',load_catalog())
        self.store.add(A,'Empresa A');self.store.add(B,'Empresa B')

    def jobs(self):
        return [{**c,'relatorios':self.store.settings(c['cnpj'])} for c in self.store.companies()]


class DomainTests(unittest.TestCase):
    def test_cnpj_digitos_e_zeros(self):
        self.assertEqual(cnpj(A),A);self.assertTrue(A.startswith('00'))
        punct=f'{A[:2]}.{A[2:5]}.{A[5:8]}/{A[8:12]}-{A[12:]}'
        self.assertEqual(cnpj(punct),A)
        for invalid in ['0'*14,A[:-1]+str((int(A[-1])+1)%10),'12','abc'+A]:
            with self.assertRaises(ValueError):cnpj(invalid)

    def test_periodo_bissexto(self):
        self.assertEqual(str(period('02/2024')[1]),'2024-02-29')
        for invalid in ['13/2026','1/2026','00/2026','10-2026']:
            with self.assertRaises(ValueError):period(invalid)

    def test_barra_competencia_e_exclusao(self):
        self.assertEqual(format_competence('10'),'10/')
        self.assertEqual(format_competence('102026'),'10/2026')
        self.assertEqual(format_competence('10/2026'),'10/2026')
        self.assertEqual(format_competence('10',deleting=True),'10')

    def test_nomes_e_redacao(self):
        self.assertEqual(filename('Operações Próprias.pdf'),'Operações Próprias.pdf')
        for invalid in ['../x.pdf','CON.pdf','x?.pdf','x.pdf ',' .pdf','x.txt']:
            with self.assertRaises(ValueError):filename(invalid)
        self.assertNotEqual(folder_name('Empresa',A),folder_name('Empresa',B))
        self.assertNotIn(A,json.dumps(redact({'x':[A]})))

    def test_nome_duplicado_e_difal(self):
        rows=[{**r,'selecionado':r['id'] in DEFAULTS} for r in load_catalog()]
        selected=[r for r in rows if r['selecionado']]
        selected[1]['nome_pdf']=selected[0]['nome_pdf'].upper()
        with self.assertRaises(ValueError):validate_settings(rows)
        with self.assertRaises(ValueError):validate_settings([{'id':'x','nome_pdf':'x.pdf','selecionado':True,'caminho_pva':['Escrituração Fiscal','DIFAL RJ']}])


class StorageTests(Fixture):
    def test_persistencia_e_padrao_exato(self):
        again=Store(self.root/'db.sqlite3',load_catalog())
        self.assertEqual(len(again.companies()),2)
        for company in (A,B):self.assertEqual({r['id'] for r in again.settings(company) if r['selecionado']},DEFAULTS)

    def test_isolamento_e_padrao_preserva_nome(self):
        rows=self.store.settings(A)
        rows[0]['nome_pdf']='Personalizado ç.pdf';rows[4]['selecionado']=True
        self.store.save_settings(A,rows);self.store.defaults(A)
        self.assertEqual(self.store.settings(A)[0]['nome_pdf'],'Personalizado ç.pdf')
        self.assertNotEqual(self.store.settings(B)[0]['nome_pdf'],'Personalizado ç.pdf')
        self.assertEqual({r['id'] for r in self.store.settings(A) if r['selecionado']},DEFAULTS)

    def test_duplicado_nao_sobrescreve(self):
        rows=self.store.settings(A);rows[0]['nome_pdf']='Meu.pdf';self.store.save_settings(A,rows)
        self.assertFalse(self.store.add(A,'Outro nome'))
        self.assertEqual(self.store.companies('Empresa A')[0]['name'],'Empresa A')
        self.assertEqual(self.store.settings(A)[0]['nome_pdf'],'Meu.pdf')

    def test_edicao_cnpj_cascata_exclusao_e_pesquisa(self):
        new=number('221234560001');self.store.edit(A,new,'Nome novo')
        self.assertEqual(len(self.store.settings(new)),29)
        self.assertEqual(self.store.companies('221234')[0]['cnpj'],new)
        self.store.delete(new);self.assertEqual(self.store.settings(new),[])

    def test_todos_obrigatorios_inclusive_cf(self):
        rows=self.store.settings(A)
        for row in rows:
            row['opcional']=True
        self.store.save_settings(A,rows)
        self.assertTrue(all(not r['opcional'] for r in self.store.settings(A)))

    def test_migracao_preserva_selecao_e_nomes(self):
        rows=self.store.settings(A);rows[0]['nome_pdf']='Meu nome.pdf';self.store.save_settings(A,rows)
        with self.store.connect() as db:db.execute('UPDATE setting SET optional=1')
        again=Store(self.root/'db.sqlite3',load_catalog())
        self.assertEqual(again.settings(A)[0]['nome_pdf'],'Meu nome.pdf')
        self.assertEqual({r['id'] for r in again.settings(A) if r['selecionado']},DEFAULTS)
        with again.connect() as db:self.assertEqual(db.execute('SELECT SUM(optional) FROM setting').fetchone()[0],0)

    def test_config_nao_altera_regras_java(self):
        rows=self.store.settings(A)
        original=deepcopy(rows[2]['caminho_pva'])
        rows[2]['exibir_subrelatorios']=False;rows[2]['caminho_pva']=['Nome inventado']
        self.store.save_settings(A,rows)
        again=self.store.settings(A)[2]
        self.assertTrue(again['exibir_subrelatorios']);self.assertEqual(again['caminho_pva'],original)

    def test_catalogo_novo_sem_modificar_config(self):
        rows=discovered([['Escrituração Fiscal','Categoria real','Novo relatório']],self.store.catalog())
        self.store.update_catalog(rows)
        config=self.store.settings(A)
        self.assertEqual(len(config),30);self.assertFalse(config[-1]['selecionado'])
        self.assertEqual(config[-1]['nome_pdf'],'Novo relatório.pdf')
        self.assertEqual(len([r for r in config if r['selecionado']]),5)


class ImportTests(Fixture):
    def test_csv_primeira_linha_acentos_cp1252_e_rejeicoes(self):
        new=number('331234560001')
        path=self.root/'empresas.csv'
        path.write_bytes(f'{new};Empresa São João\n{A};Não substituir\n\nCNPJ;Nome\n123;Inválida\n'.encode('cp1252'))
        result=import_companies(path,self.store)
        self.assertEqual((result['importadas'],result['existentes'],result['rejeitadas']),(1,1,2))
        self.assertEqual([r['linha'] for r in result['rejeicoes']],[4,5])
        self.assertEqual(self.store.companies('São João')[0]['cnpj'],new)
        self.assertEqual({r['id'] for r in self.store.settings(new) if r['selecionado']},DEFAULTS)

    def test_csv_virgula_utf8_com_nome_entre_aspas(self):
        new=number('441234560001');path=self.root/'empresas.csv'
        path.write_text(f'{new},"Nome, com vírgula"\n',encoding='utf-8-sig')
        result=import_companies(path,self.store);self.assertEqual(result['importadas'],1)

    def test_numerico_sem_inventar_zeros(self):
        self.assertEqual(numeric_cnpj(int(B)),B)
        self.assertEqual(numeric_cnpj(int(A),'00000000000000'),A)
        self.assertEqual(numeric_cnpj(int(A),'00"."000"."000"/"0000"-"00'),A)
        for value,fmt in [(int(A),'General'),(1.5,''),(True,''),(10**14,'')]:
            with self.assertRaises(ValueError):numeric_cnpj(value,fmt)

    def test_xlsm_valores_e_mascara_sem_macros(self):
        import openpyxl
        path=self.root/'empresas.xlsm';book=openpyxl.Workbook();sheet=book.active
        sheet.append([int(A),'Não substituir']);sheet['A1'].number_format='00000000000000'
        new=number('551234560001');sheet.append([new,'Nova importada']);sheet.append([int(A),'Sem máscara']);book.save(path);book.close()
        result=import_companies(path,self.store)
        self.assertEqual((result['importadas'],result['existentes'],result['rejeitadas']),(1,1,1))

    def test_xls_adaptador_preserva_mascara_e_libera_arquivo(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        import xlrd
        sheet=SimpleNamespace(nrows=1,ncols=2,cell=lambda r,c:SimpleNamespace(ctype=xlrd.XL_CELL_NUMBER,value=int(A),xf_index=0),cell_value=lambda r,c:'Empresa')
        book=SimpleNamespace(sheet_by_index=lambda i:sheet,xf_list=[SimpleNamespace(format_key=1)],
                             format_map={1:SimpleNamespace(format_str='00000000000000')},release_resources=Mock())
        with patch('xlrd.open_workbook',return_value=book):result=list(rows(self.root/'sample.xls'))
        self.assertEqual(numeric_cnpj(result[0][1],result[0][3]),A);book.release_resources.assert_called_once()

    def test_arquivo_invalido_nao_destroi_cadastro(self):
        path=self.root/'invalido.xls';path.write_bytes(b'nao e um xls')
        self.assertIn('erro_arquivo',import_companies(path,self.store));self.assertEqual(len(self.store.companies()),2)

    def test_tooltip_layout(self):
        self.assertIn('Não utilizar cabeçalho.',HELP);self.assertIn('Coluna A: CNPJ',HELP)


class FakePVA:
    def __init__(self,stop=None,fail=None,missing=None,close_failure=False):
        self.active=None;self.calls=[];self.stop=stop;self.fail=fail;self.missing=missing;self.close_failure=close_failure
    def estado(self,criteria,folder):
        self.calls.append(('estado',criteria['cnpj']))
        if self.active is None:return {'aberta':False,'pode_abrir':True,'janela':[1,2]}
        return {'aberta':True,'janela':[1,2],'rodape_lido':True,'identidade_aberta_confirmada':self.active==criteria['cnpj']}
    def abrir(self,criteria,identity,folder):
        self.calls.append(('abrir',criteria['cnpj']))
        if self.missing==criteria['cnpj']:return {'correspondencia_unica':False}
        self.active=criteria['cnpj'];return {'correspondencia_unica':True,'selecao_confirmada':True,'ok_tentativas':1,'identidade_aberta_confirmada':True}
    def identificar(self):return (1,2)
    def report(self,case,folder):
        self.calls.append(('relatorio',case['id']))
        if case['id']==self.fail:return {'sucesso':False}
        import pymupdf
        path=Path(case['destino']);doc=pymupdf.open();doc.new_page().insert_text((50,50),'PDF offline de teste');doc.save(path);doc.close()
        if self.stop:self.stop.set()
        return {'sucesso':True}
    def close(self,criteria,folder):
        self.calls.append(('fechar',criteria['cnpj']))
        if self.close_failure:return {'sucesso':False}
        self.active=None;return {'sucesso':True,'fechamento_confirmado':True}


class ProcessingTests(Fixture):
    def process(self,pva,stop=None,jobs=None):
        return Processor(pva,stop=stop,temporary_root=self.root/'temporarios').run(jobs or self.jobs(),'10/2026',self.root/'saida',self.root/'run')

    def test_duas_empresas_pdf_validado_ordem_fechamento_e_privacidade(self):
        pva=FakePVA();summary=self.process(pva)
        self.assertTrue(summary['sucesso']);self.assertEqual(summary['pdfs'],10)
        actions=[c for c in pva.calls if c[0] in {'abrir','fechar'}]
        self.assertEqual(actions,[('abrir',A),('fechar',A),('abrir',B),('fechar',B)])
        self.assertEqual([c[1] for c in pva.calls if c[0]=='relatorio'],
            ['documentos_entradas','documentos_saidas','operacoes_proprias','operacoes_st','recibo']*2)
        for number in (A,B):self.assertEqual(len(list((self.root/'saida/2026-10'/folder_name('Empresa A' if number==A else 'Empresa B',number)).glob('*.pdf'))),5)
        for file in (self.root/'run').rglob('*'):
            if file.suffix in {'.json','.csv','.txt'}:
                text=file.read_text('utf-8-sig');self.assertNotIn(A,text);self.assertNotIn(B,text)
        for folder in [self.root/'run',self.root/'run/empresa_001',self.root/'run/empresa_002']:
            self.assertTrue((folder/'resumo.json').exists());self.assertTrue((folder/'resumo.csv').exists())

    def test_inicio_com_escrituracao_nao_fecha(self):
        pva=FakePVA();pva.active=B
        self.assertFalse(self.process(pva)['sucesso'])
        self.assertFalse(any(c[0] in {'abrir','fechar','relatorio'} for c in pva.calls))

    def test_nova_tentativa_reutiliza_escrituracao_apos_falha(self):
        pva=FakePVA(fail='documentos_entradas')
        failed=self.process(pva)
        self.assertFalse(failed['sucesso']);self.assertEqual(pva.active,A)
        before=len(pva.calls);pva.fail=None
        retried=Processor(pva,temporary_root=self.root/'temporarios2').run(self.jobs(),'10/2026',self.root/'saida',self.root/'run2')
        self.assertTrue(retried['sucesso']);self.assertTrue(retried['empresas'][0]['escrituracao_reutilizada'])
        self.assertNotIn(('abrir',A),pva.calls[before:])
        self.assertEqual(retried['pdfs'],10)

    def test_falha_relatorio_nao_fecha_nem_abre_proxima(self):
        pva=FakePVA(fail='documentos_saidas');summary=self.process(pva)
        self.assertFalse(summary['sucesso']);self.assertEqual(summary['pdfs'],1)
        self.assertNotIn(('abrir',B),pva.calls);self.assertFalse(any(c[0]=='fechar' for c in pva.calls))
        self.assertEqual(len([c for c in pva.calls if c==('relatorio','documentos_saidas')]),1)

    def test_parar_depois_pdf_seguro_deixa_escrituracao(self):
        stop=threading.Event();pva=FakePVA(stop=stop);summary=self.process(pva,stop)
        self.assertTrue(summary['interrompida']);self.assertEqual(summary['pdfs'],1)
        self.assertEqual(summary['empresas'][0]['status'],'Interrompida');self.assertEqual(pva.active,A)
        self.assertFalse(any(c[0]=='fechar' for c in pva.calls))

    def test_fechamento_falha_nao_abre_proxima(self):
        pva=FakePVA(close_failure=True);self.assertFalse(self.process(pva)['sucesso'])
        self.assertNotIn(('abrir',B),pva.calls)

    def test_rodape_divergente_depois_abertura_nao_gera_nem_fecha(self):
        pva=FakePVA();normal=pva.abrir
        def wrong(*args):
            result=normal(*args);pva.active=B;return result
        pva.abrir=wrong;summary=self.process(pva)
        self.assertFalse(summary['sucesso']);self.assertEqual(summary['pdfs'],0)
        self.assertFalse(any(c[0] in {'relatorio','fechar'} for c in pva.calls))

    def test_falha_tecnica_na_abertura_nao_avanca_empresa(self):
        pva=FakePVA()
        def broken(criteria,identity,folder):
            pva.calls.append(('abrir',criteria['cnpj']))
            return {'erro_tipo':'FileNotFoundError'}
        pva.abrir=broken;summary=self.process(pva)
        self.assertFalse(summary['sucesso']);self.assertEqual(summary['pdfs'],0)
        self.assertNotIn(('abrir',B),pva.calls)
        self.assertIn('componente',summary['motivo'])

    def test_ausencia_empresa_so_continua_com_pva_vazio(self):
        pva=FakePVA(missing=A);summary=self.process(pva)
        self.assertFalse(summary['sucesso']);self.assertEqual(summary['empresas'][1]['status'],'Concluída')
        self.assertEqual(summary['pdfs'],5)

    def test_existente_nao_acessa_pva(self):
        jobs=self.jobs();folder=self.root/'saida/2026-10'/folder_name('Empresa A',A);folder.mkdir(parents=True)
        target=folder/jobs[0]['relatorios'][0]['nome_pdf'];target.write_bytes(b'original')
        pva=FakePVA();self.assertFalse(self.process(pva)['sucesso']);self.assertEqual(pva.calls,[])
        self.assertEqual(target.read_bytes(),b'original')

    def test_indisponivel_obrigatorio_interrompe(self):
        configs=self.store.settings(B)
        for r in configs:r['selecionado']=r['id']=='controle_creditos_fiscais'
        self.store.save_settings(B,configs)
        pva=FakePVA();original=pva.report
        def report(case,folder):
            if case['id']=='controle_creditos_fiscais':return {'sucesso':True,'ignorado':True}
            return original(case,folder)
        pva.report=report;summary=self.process(pva)
        self.assertFalse(summary['sucesso']);self.assertEqual(summary['pdfs'],5)
        self.assertEqual(summary['empresas'][1]['relatorios'][0]['status'],'falha')

    def test_pdf_invalido_bloqueia_sem_publicar(self):
        pva=FakePVA()
        def invalid(case,folder):Path(case['destino']).write_bytes(b'invalid');return {'sucesso':True}
        pva.report=invalid;summary=self.process(pva)
        self.assertFalse(summary['sucesso']);self.assertEqual(summary['pdfs'],0)
        self.assertEqual(list((self.root/'saida').rglob('*.pdf')),[])

    def test_publish_nao_sobrescreve(self):
        src=self.root/'src';dst=self.root/'dst';src.write_bytes(b'new');dst.write_bytes(b'old')
        with self.assertRaises(FileExistsError):publish(src,dst)
        self.assertEqual(dst.read_bytes(),b'old');self.assertTrue(src.exists())


class GUITests(Fixture):
    def test_construcao_tres_abas_sem_pva(self):
        import tkinter as tk
        from app.gui import App
        root=tk.Tk();root.withdraw()
        try:
            app=App(root,self.store);root.update_idletasks()
            self.assertEqual(len(app.tabs.tabs()),3)
            self.assertEqual(len(app.process_tree.get_children()),2)
            self.assertEqual({r['id'] for r in app.rows if r['selecionado']},DEFAULTS)
            app.set_busy(True);self.assertEqual(str(app.start_button['state']),'disabled')
            app.set_busy(False);app.select_companies(True);self.assertEqual(app.selected,{A,B})
        finally:root.destroy()

    def test_clique_texto_nao_marca_caixa_marca(self):
        import tkinter as tk
        from types import SimpleNamespace
        from app.gui import App
        root=tk.Tk();root.withdraw()
        try:
            app=App(root,self.store);event=SimpleNamespace(x=20,y=20)
            for tree,handler,id,check in [
                (app.process_tree,app.toggle_company,A,lambda:A in app.selected),
                (app.report_tree,app.toggle_report,next(iter(app.report_by_iid)),lambda:app.rows[0]['selecionado'])]:
                before=check()
                with patch.object(tree,'identify_column',return_value='#0'),patch.object(tree,'identify_row',return_value=id):
                    with patch.object(tree,'identify_element',return_value='Treeitem.text'):handler(event)
                    self.assertEqual(check(),before)
                    with patch.object(tree,'identify_element',return_value='Treeitem.image'):handler(event)
                    self.assertNotEqual(check(),before)
            self.assertEqual(tuple(app.report_tree['columns']),('pdf',))
        finally:root.destroy()


class MenuTests(unittest.TestCase):
    def test_para_na_barra_sem_entrar_visualizador(self):
        from types import SimpleNamespace as Node
        from backend_empresa import locate_menu
        menu=Node(role_en_us='menu',name='Escrituração Fiscal',kids=[])
        bar=Node(role_en_us='menu bar',kids=[menu])
        viewer=Node(role_en_us='panel',kids=None)
        root=Node(role_en_us='frame',kids=[bar,viewer])
        def children(node):
            if node is viewer:raise AssertionError('Não percorrer o visualizador após localizar o menu.')
            return node.kids
        self.assertIs(locate_menu(root,children),menu)


class LockTests(Fixture):
    def test_trava_morta_sem_auxiliar_e_arquivada(self):
        from app.locks import recover_stale
        path=self.root/'automacao_ativa.lock';path.write_text('{"pid":123}',encoding='utf-8')
        archived=recover_stale(self.root,alive=lambda pid:False,auxiliaries=lambda:False)
        self.assertEqual(len(archived),1);self.assertFalse(path.exists())

    def test_pid_vivo_ou_auxiliar_preserva_trava(self):
        from app.locks import recover_stale
        path=self.root/'automacao_ativa.lock';path.write_text('{"pid":123}',encoding='utf-8')
        self.assertEqual(recover_stale(self.root,alive=lambda pid:True,auxiliaries=lambda:False),[])
        self.assertEqual(recover_stale(self.root,alive=lambda pid:False,auxiliaries=lambda:True),[])
        self.assertTrue(path.exists())


if __name__=='__main__':unittest.main()
