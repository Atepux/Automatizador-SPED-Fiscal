from pathlib import Path
import sys
import unittest

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
from diagnostico_escrituracoes import safe_name


class PrivacidadeTests(unittest.TestCase):
    def test_rotulos_fixos_preservados(self):
        for label in ['CNPJ','Período','Abrir','Fechar','Escrituração Fiscal']:
            self.assertEqual(safe_name(label),label)

    def test_dados_dinamicos_omitidos(self):
        for label in ['00.000.000/0000-00','00000000000000','Empresa exemplo','01/10/2026 a 31/10/2026','CNPJ: 00.000.000/0000-00']:
            self.assertEqual(safe_name(label),'[omitido]')


if __name__=='__main__':unittest.main()
