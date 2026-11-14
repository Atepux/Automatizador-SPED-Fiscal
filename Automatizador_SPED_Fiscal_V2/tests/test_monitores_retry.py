from pathlib import Path
import json,sys,tempfile,unittest
from types import SimpleNamespace
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'scripts'))
from app.coordinates import valid_bounds,in_desktop
from app.locks import release_owned
from backend_empresa import BackendJava


class MonitorTests(unittest.TestCase):
    def test_coordenada_do_erro_e_valida_no_monitor_esquerdo(self):
        bounds={'x':-1859,'y':176,'width':245,'height':18}
        self.assertTrue(valid_bounds(bounds))
        self.assertTrue(in_desktop((-1737,185),(-1920,0,3840,1080)))

    def test_monitor_acima_e_limites_invalidos(self):
        self.assertTrue(valid_bounds({'x':100,'y':-900,'width':100,'height':18}))
        self.assertTrue(in_desktop((150,-890),(0,-1080,1920,2160)))
        self.assertFalse(valid_bounds({'x':-1,'y':-1,'width':0,'height':18}))
        self.assertFalse(valid_bounds({'x':float('nan'),'y':0,'width':100,'height':18}))
        self.assertFalse(in_desktop((-3000,50),(-1920,0,3840,1080)))


class RetryLockTests(unittest.TestCase):
    def test_falha_sem_auxiliar_libera_na_mesma_sessao(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            for file in ('automacao_ativa.lock','multiempresas_ativa.lock'):
                (root/file).write_text('{"pid":123}',encoding='utf-8')
            self.assertTrue(release_owned(root,123,[]))
            self.assertEqual(list(root.glob('*.lock')),[])

    def test_auxiliar_ativo_e_trava_de_outra_execucao_sao_preservados(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);file=root/'automacao_ativa.lock'
            file.write_text('{"pid":123}',encoding='utf-8')
            self.assertFalse(release_owned(root,123,[456]));self.assertTrue(file.exists())
            self.assertFalse(release_owned(root,999,[]));self.assertTrue(file.exists())

    def test_termino_de_auxiliar_e_detectado_sem_reiniciar(self):
        backend=BackendJava();state=[None]
        process=SimpleNamespace(pid=456,poll=lambda:state[0])
        backend.track(process);self.assertEqual(backend.pending_workers(),[456])
        state[0]=0;self.assertEqual(backend.pending_workers(),[])


if __name__=='__main__':unittest.main()
