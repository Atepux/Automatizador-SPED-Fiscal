import json
from pathlib import Path
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
from empresa_unica import executar,destino_empresa,revisao_offline
import geracao_v1


def aberta(**extra):
    return {'aberta':True,'janela':[100,200],'rodape_lido':True,
            'identidade_aberta_confirmada':True,**extra}


class FakeBackend:
    def __init__(self,estados,abertura=None):
        self.estados = iter(estados); self.chamadas = []; self.abertura = abertura
    def estado(self,criteria,folder):
        self.chamadas.append('estado'); return next(self.estados)
    def abrir(self,criteria,identity,folder):
        self.chamadas.append('abrir'); return self.abertura
    def identificar(self):
        self.chamadas.append('identificar'); return (100,200)


class EmpresaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.criteria = {'cnpj':'00000000000000','inicio':'01/10/2026','fim':'31/10/2026'}
        self.cases = []

    def runner(self,folder,case):
        self.cases.append(case)
        return {'sucesso':True,'pdf':{'tamanho_bytes':123,'paginas':1},'total_segundos':.1}

    def run_case(self,backend,runner=None):
        return executar(self.criteria,'EMPRESA_TESTE',self.root/'saida',self.root/'run',backend,runner or self.runner)

    def test_reutiliza_sem_abrir_e_preserva_regras(self):
        backend = FakeBackend([aberta(),aberta()])
        summary = self.run_case(backend)
        self.assertTrue(summary['sucesso']); self.assertNotIn('abrir',backend.chamadas)
        self.assertTrue(summary['escrituracao_reutilizada'])
        self.assertEqual([c['id'] for c in self.cases],geracao_v1.ORDEM)
        self.assertEqual([c['id'] for c in self.cases if c['exibir_subrelatorios']],['operacoes_proprias','operacoes_st'])
        self.assertEqual(self.cases[-1]['timeout_abertura_segundos'],5)
        for case in self.cases:
            self.assertEqual(Path(case['destino']).parent,self.root/'saida/EMPRESA_TESTE/2026-10')
            self.assertFalse(any('difal' in p.lower() for p in case['caminho_pva']))
        self.assertTrue((self.root/'run/resumo.csv').exists())
        saved=json.loads((self.root/'run/resumo.json').read_text('utf-8'))
        self.assertEqual(len(saved['relatorios']),8)
        for path in (self.root/'run').rglob('*'):
            if path.is_file(): self.assertNotIn(self.criteria['cnpj'],path.read_text('utf-8-sig'))

    def test_abre_so_quando_vazia_e_confirma_rodape(self):
        backend = FakeBackend([{'aberta':False,'pode_abrir':True,'janela':[100,200]},aberta()],
            {'correspondencia_unica':True,'selecao_confirmada':True,'ok_tentativas':1,'identidade_aberta_confirmada':True})
        summary=self.run_case(backend)
        self.assertTrue(summary['sucesso']); self.assertEqual(backend.chamadas.count('abrir'),1)
        self.assertFalse(summary['escrituracao_reutilizada'])

    def test_outra_escrituracao_interrompe_sem_abrir(self):
        backend = FakeBackend([aberta(identidade_aberta_confirmada=False)])
        self.assertFalse(self.run_case(backend)['sucesso'])
        self.assertEqual(backend.chamadas,['estado']); self.assertEqual(self.cases,[])

    def test_rodape_ilegivel_interrompe(self):
        backend=FakeBackend([aberta(rodape_lido=False)])
        self.assertFalse(self.run_case(backend)['sucesso']); self.assertEqual(self.cases,[])

    def test_modal_ou_erro_ou_ambiguidade_interrompem(self):
        # Cada caso usa uma pasta independente; nenhuma acao real de interface.
        for i,state in enumerate([aberta(modal_aberta=True),aberta(timeout=True),
                                  aberta(erro_tipo='Erro'),{'janela':[100,200]}]):
            with self.subTest(i=i):
                backend=FakeBackend([state])
                summary=executar(self.criteria,'EMPRESA_TESTE',self.root/'saida',self.root/f'run{i}',backend,self.runner)
                self.assertFalse(summary['sucesso']); self.assertNotIn('abrir',backend.chamadas)
        self.assertEqual(self.cases,[])

    def test_abertura_sem_confirmacao_ou_duplicidade_nao_gera(self):
        for i,result in enumerate([{'correspondencia_unica':False},{'timeout':True},
             {'correspondencia_unica':True,'selecao_confirmada':True,'ok_tentativas':1,
              'identidade_aberta_confirmada':True,'worker_pendente':True}]):
            backend=FakeBackend([{'aberta':False,'pode_abrir':True,'janela':[100,200]}],result)
            summary=executar(self.criteria,'EMPRESA_TESTE',self.root/'saida',self.root/f'run{i}',backend,self.runner)
            self.assertFalse(summary['sucesso'])
        self.assertEqual(self.cases,[])

    def test_divergencia_antes_geracao_interrompe(self):
        self.assertFalse(self.run_case(FakeBackend([aberta(),aberta(identidade_aberta_confirmada=False)]))['sucesso'])
        self.assertEqual(self.cases,[])

    def test_nao_sobrescreve_nem_acessa_pva_se_destino_existe(self):
        destino=destino_empresa(self.root/'saida','EMPRESA_TESTE',self.criteria)
        destino.mkdir(parents=True)
        file=destino/geracao_v1.carregar_cadastro()[0]['nome_pdf']; file.write_bytes(b'original')
        backend=FakeBackend([])
        self.assertFalse(self.run_case(backend)['sucesso'])
        self.assertEqual(backend.chamadas,[]); self.assertEqual(file.read_bytes(),b'original')

    def test_relatorio_indisponivel_obrigatorio_interrompe(self):
        def runner(folder,case):
            if case['id']=='controle_creditos_fiscais':
                self.cases.append(case); return {'sucesso':True,'ignorado':True}
            return self.runner(folder,case)
        summary=self.run_case(FakeBackend([aberta(),aberta()]),runner)
        self.assertFalse(summary['sucesso']); self.assertEqual(len(self.cases),6)
        self.assertEqual(summary['relatorios'][5]['erro_tipo'],'RelatorioObrigatorioAusente')

    def test_erro_real_interrompe_sem_repeticao(self):
        def runner(folder,case):
            self.cases.append(case); return {'sucesso':False,'erro_tipo':'FalhaSimulada'}
        summary=self.run_case(FakeBackend([aberta(),aberta()]),runner)
        self.assertFalse(summary['sucesso']); self.assertEqual(len(self.cases),1)
        self.assertTrue(all(r['status']=='não executado' for r in summary['relatorios'][1:]))

    def test_manifesto_cadastro_e_importacoes_independentes(self):
        self.assertTrue(revisao_offline()['aprovado'])

    def test_pasta_empresa_invalida_e_multicompetencia(self):
        for alias in ['..','A/B','CON','00000000000000']:
            with self.assertRaises(ValueError): destino_empresa(self.root,alias,self.criteria)
        with self.assertRaises(ValueError): destino_empresa(self.root,'EMPRESA_TESTE',{**self.criteria,'fim':'30/11/2026'})


if __name__=='__main__': unittest.main()
