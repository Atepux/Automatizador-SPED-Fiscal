import sys
from pathlib import Path
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from subrelatorios import confirmar_checkbox
from poc_ponta_a_ponta import exigir_prontidao_ativacao


class RegraSimplesTests(unittest.TestCase):
    def test_ja_marcada_nao_clica(self):
        action=Mock();r=confirmar_checkbox(Mock(side_effect=[True,True]),action)
        action.assert_not_called();self.assertFalse(r['alterado'])

    def test_desmarcada_marca_uma_vez(self):
        action=Mock();r=confirmar_checkbox(Mock(side_effect=[False,True]),action)
        action.assert_called_once();self.assertTrue(r['final']);self.assertTrue(r['alterado'])

    def test_nao_confirmada_interrompe_sem_retry(self):
        action=Mock()
        with self.assertRaises(RuntimeError):confirmar_checkbox(Mock(side_effect=[False,False]),action)
        action.assert_called_once()

    def test_erro_leitura_propaga(self):
        action=Mock()
        with self.assertRaises(OSError):confirmar_checkbox(Mock(side_effect=OSError()),action)
        action.assert_not_called()

    def test_timeout_acao_propaga(self):
        action=Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError):confirmar_checkbox(Mock(return_value=False),action)
        action.assert_called_once()

    def test_confirmacao_final_nao_pode_marcar(self):
        action=Mock()
        with self.assertRaises(RuntimeError):confirmar_checkbox(Mock(return_value=False),action,False)
        action.assert_not_called()

    def test_checkbox_e_salvar_bastam_sem_estabilidade(self):
        exigir_prontidao_ativacao({'sucesso':True,'subrelatorios':{'final':True,'salvar_habilitado':True}},True)

    def test_falhas_bloqueiam_exportacao(self):
        cases=[{'sucesso':False},{'sucesso':True,'erro_tipo':'TimeoutError'},
               {'sucesso':True,'subrelatorios':None},
               {'sucesso':True,'subrelatorios':{'final':False,'salvar_habilitado':True}},
               {'sucesso':True,'subrelatorios':{'final':True,'salvar_habilitado':False}}]
        for case in cases:
            with self.subTest(case=case),self.assertRaises(RuntimeError):exigir_prontidao_ativacao(case,True)


if __name__=='__main__':unittest.main()
