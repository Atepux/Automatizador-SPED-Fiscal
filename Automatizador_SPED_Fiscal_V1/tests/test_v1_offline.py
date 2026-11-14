"""Nao acessa o PVA; processos/identificacao e geracao sao substituidos."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import principal as v1


class V1Tests(unittest.TestCase):
    def setUp(self):self.cases=v1.carregar_cadastro()

    def test_order_and_original_names(self):
        self.assertEqual([r['id'] for r in self.cases],v1.ORDEM)
        self.assertEqual(self.cases[2]['nome_pdf'],'Registros Fiscais da Apuração do ICMS_Operações Próprias.pdf')
        self.assertEqual(self.cases[3]['nome_pdf'],'Registros Fiscais da Apuração do ICMS_Operações ST.pdf')
        self.assertEqual(sum(r['exibir_subrelatorios'] for r in self.cases),2)
        self.assertEqual(self.cases[-1]['timeout_abertura_segundos'],5)

    def test_conflict_blocks_before_identification_and_runner(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dest=root/'destino';dest.mkdir();run=root/'logs';run.mkdir()
            (dest/self.cases[0]['nome_pdf']).write_bytes(b'preexistente')
            def forbidden(*a):raise AssertionError('Nao deve chamar UI/runner')
            with self.assertRaises(FileExistsError):v1.executar_lote(self.cases,dest,run,forbidden,forbidden)
            self.assertEqual((dest/self.cases[0]['nome_pdf']).read_bytes(),b'preexistente')

    def execute_fake(self,result_for,identity=lambda:(1,2)):
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(temp);run=root/'logs';run.mkdir();called=[]
            def fake(folder,case):
                called.append(case)
                self.assertEqual(case['nome_pdf'],Path(case['destino']).name)
                self.assertFalse(case['exigir_marcadores'])
                return result_for(case)
            summary=v1.executar_lote(self.cases,root/'Empresa com espaços',run,fake,identity)
            self.assertTrue((run/'resumo.json').is_file());self.assertTrue((run/'resumo.csv').is_file())
            self.assertEqual(json.loads((run/'resumo.json').read_text('utf-8'))['sucesso'],summary['sucesso'])
            return summary,called

    def test_all_eight_sequential_no_intervention(self):
        summary,calls=self.execute_fake(lambda c:{'sucesso':True,'pdf':{'tamanho_bytes':100,'paginas':1},'total_segundos':1})
        self.assertTrue(summary['sucesso']);self.assertEqual([c['id'] for c in calls],v1.ORDEM)

    def test_optional_missing_does_not_stop(self):
        summary,calls=self.execute_fake(lambda c:{'sucesso':True,'ignorado':True} if c.get('opcional') else {'sucesso':True,'pdf':{'paginas':1}})
        self.assertTrue(summary['sucesso']);self.assertEqual(len(calls),8)
        self.assertEqual(summary['relatorios'][5]['status'],'ignorado — indisponível')

    def test_error_stops_without_retry(self):
        summary,calls=self.execute_fake(lambda c:{'sucesso':False,'erro_tipo':'RuntimeError'} if c['id']=='documentos_saidas' else {'sucesso':True,'pdf':{'paginas':1}})
        self.assertFalse(summary['sucesso']);self.assertEqual(len(calls),2)
        self.assertEqual(summary['relatorios'][2]['status'],'não executado')

    def test_identity_change_stops_before_next_report(self):
        count=0
        def identify():
            nonlocal count
            count+=1
            return (1,2) if count<=2 else (1,3)
        summary,calls=self.execute_fake(lambda c:{'sucesso':True},identify)
        self.assertFalse(summary['sucesso']);self.assertEqual(len(calls),1)

    def test_worker_pending_blocks_next_report(self):
        summary,calls=self.execute_fake(lambda c:{'sucesso':True,'A_permanece_vivo':True})
        self.assertFalse(summary['sucesso']);self.assertTrue(summary['workers_pendentes']);self.assertEqual(len(calls),1)

    def test_bad_config_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);(base/'config').mkdir()
            path=base/'config/relatorios.json'
            for kind in ['duplicate','difal','subreports','order']:
                data=json.loads(json.dumps(self.cases))
                if kind=='duplicate':data[1]['nome_pdf']=data[0]['nome_pdf']
                elif kind=='difal':data[0]['caminho_pva']=['Escrituração Fiscal','DIFAL RJ']
                elif kind=='subreports':data[0]['exibir_subrelatorios']=True
                else:data.reverse()
                path.write_text(json.dumps({'relatorios':data}),encoding='utf-8')
                with self.subTest(kind=kind),self.assertRaises(v1.ConfiguracaoInvalida):v1.carregar_cadastro(base)

    def test_imported_routines_are_independent_and_unchanged(self):
        check=v1.revisao_offline()
        self.assertTrue(check['aprovado'],check['falhas'])
        self.assertEqual(len(check['rotinas_independentes']),9)
        self.assertFalse(check['PVA_acessado'])


if __name__=='__main__':unittest.main()
