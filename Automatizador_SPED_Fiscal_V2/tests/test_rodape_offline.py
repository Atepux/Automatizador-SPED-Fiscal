import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from rodape_escrituracao import compare, wait_main_ready


class RodapeTests(unittest.TestCase):
    criteria = {'cnpj':'00000000000000','inicio':'01/10/2026','fim':'31/10/2026'}
    text = 'CNPJ: 00.000.000/0000-00 Período: 01/10/2026 a 31/10/2026'

    def test_identidade_exata(self):
        self.assertTrue(compare(self.text,self.criteria))

    def test_divergencia_ou_ausencia_interrompe(self):
        for value in ['', self.text.replace('31/10','30/10'),
                      self.text.replace('0000-00','0000-01'),
                      self.text+' 01/01/2026', self.text+' 11.111.111/1111-11']:
            self.assertFalse(compare(value,self.criteria))

    def test_modal_transitoria_some_sem_interacao(self):
        clock = [0.0]
        wait_main_ready(lambda: [1] if clock[0]<.3 else [], lambda: True,
            timeout=1,clock=lambda:clock[0],sleep=lambda t:clock.__setitem__(0,clock[0]+t))
        self.assertLess(clock[0],1)

    def test_modal_persistente_timeout(self):
        clock = [0.0]
        with self.assertRaises(TimeoutError):
            wait_main_ready(lambda:[1],lambda:True,timeout=.3,
                clock=lambda:clock[0],sleep=lambda t:clock.__setitem__(0,clock[0]+t))


if __name__ == '__main__': unittest.main()
