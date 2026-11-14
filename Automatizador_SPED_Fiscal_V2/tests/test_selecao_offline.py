import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from selecao_escrituracao import unique, validate


class SelecaoTests(unittest.TestCase):
    def setUp(self):
        self.criteria = dict(cnpj='00000000000000', inicio='01/10/2026', fim='31/10/2026')
        self.row = {'CPF/CNPJ':'00.000.000/0000-00','Data Inicial':'01/10/2026','Data Final':'31/10/2026',
                    'Inscrição Estadual':'123','Finalidade do Arquivo':'Original','Estado':'Transmitida'}

    def test_unica_sem_depender_de_ordem(self):
        self.assertEqual(unique([(8,dict(reversed(list(self.row.items()))))],self.criteria),8)

    def test_duplicidade_interrompe(self):
        with self.assertRaisesRegex(RuntimeError,'ambigua'):
            unique([(0,self.row),(1,self.row)],self.criteria)

    def test_ausencia_interrompe(self):
        with self.assertRaises(RuntimeError): unique([],self.criteria)

    def test_periodo_divergente_interrompe(self):
        with self.assertRaises(RuntimeError): unique([(0,{**self.row,'Data Final':'30/10/2026'})],self.criteria)

    def test_ie_finalidade_desambiguam(self):
        rows=[(1,self.row),(2,{**self.row,'Inscrição Estadual':'456','Finalidade do Arquivo':'Substituto'})]
        self.assertEqual(unique(rows,{**self.criteria,'ie':'456','finalidade':'Substituto'}),2)

    def test_estado_explicito_e_exigido(self):
        self.assertEqual(unique([(1,self.row)],{**self.criteria,'estado':'transmitida'}),1)
        with self.assertRaises(RuntimeError): unique([(1,self.row)],{**self.criteria,'estado':'Validada'})

    def test_dados_invalidos_sem_valores_na_excecao(self):
        with self.assertRaisesRegex(ValueError,'cnpj_invalido'): validate({**self.criteria,'cnpj':'123'})
        with self.assertRaisesRegex(ValueError,'periodo_invalido'):
            validate({**self.criteria,'inicio':'01/11/2026'})


if __name__ == '__main__': unittest.main()
