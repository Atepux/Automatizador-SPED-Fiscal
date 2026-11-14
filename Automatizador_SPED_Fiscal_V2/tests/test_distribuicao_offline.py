from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))


TEST_CNPJ='001234560001'
for weights in ([5,4,3,2,9,8,7,6,5,4,3,2],[6,5,4,3,2,9,8,7,6,5,4,3,2]):
    remainder=sum(int(n)*w for n,w in zip(TEST_CNPJ,weights))%11
    TEST_CNPJ+=str(0 if remainder<2 else 11-remainder)


class EnvironmentTests(unittest.TestCase):
    def test_ativacao_preserva_outros_recursos_e_faz_backup(self):
        from app.environment import enable_properties,properties_enabled
        with tempfile.TemporaryDirectory() as name:
            file=Path(name)/'.accessibility.properties'
            original='outro_valor=preservar\nassistive_technologies=exemplo.OutroRecurso\n'
            file.write_text(original,encoding='latin-1')
            self.assertTrue(enable_properties(file));self.assertTrue(properties_enabled(file))
            self.assertIn('exemplo.OutroRecurso',file.read_text('latin-1'))
            self.assertIn('outro_valor=preservar',file.read_text('latin-1'))
            self.assertEqual(file.with_name(file.name+'.sped-backup').read_text('latin-1'),original)
            self.assertFalse(enable_properties(file))

    def test_detecta_tecnologia_com_espacos(self):
        from app.environment import properties_enabled
        with tempfile.TemporaryDirectory() as name:
            file=Path(name)/'props';file.write_text('assistive_technologies=outro, com.sun.java.accessibility.AccessBridge\n')
            self.assertTrue(properties_enabled(file))

    def test_auxiliar_frozen_usa_o_proprio_exe(self):
        from app import runtime
        with patch.object(runtime.sys,'frozen',True,create=True):
            command=runtime.command('scripts/backend_empresa.py','--worker','estado','pasta')
        self.assertEqual(command[1:3],['--sped-worker','scripts/backend_empresa.py'])
        self.assertNotIn('-u',command)


class InlineTests(unittest.TestCase):
    def test_edicao_na_celula_preserva_outra_empresa(self):
        import tkinter as tk
        from tkinter import ttk
        from app.gui import App
        from app.storage import Store
        from app.catalog import load_catalog
        with tempfile.TemporaryDirectory() as name:
            store=Store(Path(name)/'db.sqlite3',load_catalog())
            store.add(TEST_CNPJ,'Empresa teste')
            root=tk.Tk();root.withdraw()
            try:
                app=App(root,store)
                iid=next(iter(app.report_by_iid));row=app.report_by_iid[iid]
                original=row['nome_pdf']
                app.cell_row=row;app.cell_iid=iid;app.cell_editor=ttk.Entry(root)
                app.cell_editor.insert(0,'Nome personalizado ç.pdf')
                self.assertTrue(app.finish_inline())
                self.assertEqual(app.report_tree.item(iid,'values')[0],'Nome personalizado ç.pdf')
                self.assertEqual(store.settings(TEST_CNPJ)[0]['nome_pdf'],original)
                self.assertTrue(app.dirty)
            finally:root.destroy()

    def test_arvore_encontrada_sem_percorrer_visualizador(self):
        from types import SimpleNamespace as N
        from app.pva_worker import locate_report_tree
        tree=N(role_en_us='tree');tab=N(role_en_us='page tab',name='Relatórios',children=[tree])
        viewer=N(role_en_us='panel',name='visualizador');root=N(role_en_us='frame',children=[tab,viewer])
        def children(el):
            if el is viewer:raise AssertionError('Não percorrer o relatório aberto')
            return el.children
        self.assertIs(locate_report_tree(root,children),tree)

    def test_backup_restaura_nomes_e_selecoes(self):
        from app.storage import Store
        from app.catalog import load_catalog
        with tempfile.TemporaryDirectory() as name:
            path=Path(name);store=Store(path/'a.sqlite3',load_catalog())
            store.add(TEST_CNPJ,'Empresa teste')
            rows=store.settings(TEST_CNPJ);rows[0]['nome_pdf']='Preservar.pdf'
            store.save_settings(TEST_CNPJ,rows);store.backup(path/'backup.sqlite3')
            other=Store(path/'b.sqlite3',load_catalog());other.restore(path/'backup.sqlite3')
            self.assertEqual(other.settings(TEST_CNPJ)[0]['nome_pdf'],'Preservar.pdf')


if __name__=='__main__':unittest.main()
