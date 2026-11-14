from pathlib import Path
import sys
import unittest
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'scripts'))


class ResourceTests(unittest.TestCase):
    def test_modulos_importados_usam_recursos_centrais(self):
        from app.runtime import validate_resources
        result=validate_resources()
        self.assertEqual(len(result['modulos']),9)
        self.assertFalse(result['PVA_acessado'])

    def test_recurso_fora_da_pasta_e_bloqueado(self):
        from app.runtime import validate_resources,RESOURCES
        import selecao_escrituracao
        with patch.object(selecao_escrituracao,'ROOT',RESOURCES.parent):
            with self.assertRaisesRegex(ValueError,'raiz_de_recurso_incorreta'):
                validate_resources()


class FocusTests(unittest.TestCase):
    def test_foco_assincrono_aguarda_sem_teclas_ou_cliques(self):
        from app.win_focus import focus_window
        from types import SimpleNamespace as N
        clock=[0.0];calls=[]
        gui=N(IsIconic=lambda hwnd:False,GetForegroundWindow=lambda:99 if clock[0]>=.1 else 1,
              SetForegroundWindow=lambda hwnd:calls.append('ativar'))
        focus_window(99,gui=gui,process=N(),current_thread=7,
                     clock=lambda:clock[0],sleep=lambda t:clock.__setitem__(0,clock[0]+t))
        self.assertEqual(calls,['ativar']);self.assertGreaterEqual(clock[0],.1)

    def test_fallback_desanexa_threads(self):
        from app.win_focus import focus_window
        from types import SimpleNamespace as N
        clock=[0.0];state=[1];calls=[]
        gui=N(IsIconic=lambda hwnd:False,GetForegroundWindow=lambda:state[0],
              SetForegroundWindow=lambda hwnd:None,BringWindowToTop=lambda hwnd:state.__setitem__(0,hwnd))
        process=N(GetWindowThreadProcessId=lambda hwnd:(8,9),AttachThreadInput=lambda *args:calls.append(args))
        focus_window(99,gui=gui,process=process,current_thread=7,
                     clock=lambda:clock[0],sleep=lambda t:clock.__setitem__(0,clock[0]+t))
        self.assertEqual(calls,[(7,8,True),(7,8,False)])


if __name__=='__main__':unittest.main()
