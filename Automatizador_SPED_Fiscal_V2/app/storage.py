import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from .domain import cnpj,DEFAULTS,validate_settings,excluded


class Store:
    def __init__(self,path,catalog):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS company(cnpj TEXT PRIMARY KEY,name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS catalog(id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS setting(company TEXT REFERENCES company(cnpj) ON DELETE CASCADE ON UPDATE CASCADE,
                    report TEXT REFERENCES catalog(id),selected INTEGER NOT NULL,filename TEXT NOT NULL,optional INTEGER NOT NULL,
                    PRIMARY KEY(company,report));
                CREATE TABLE IF NOT EXISTS preference(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            ''')
            # Migracao: todos os selecionados sao obrigatorios, preservando nomes
            # e selecoes existentes. A coluna antiga fica por compatibilidade.
            db.execute('UPDATE setting SET optional=0 WHERE optional<>0')
        self.update_catalog(catalog)

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path); db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:yield db
        finally:db.close()

    def update_catalog(self,rows):
        with self.connect() as db:
            for row in rows:
                row={**row,'opcional':False}
                db.execute('INSERT INTO catalog VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
                    (row['id'],json.dumps(row,ensure_ascii=False)))
            for company in db.execute('SELECT cnpj FROM company').fetchall(): self._ensure(db,company['cnpj'])

    def catalog(self):
        with self.connect() as db: return [json.loads(r['data']) for r in db.execute('SELECT data FROM catalog ORDER BY rowid')]

    def _ensure(self,db,number):
        for record in db.execute('SELECT id,data FROM catalog').fetchall():
            row=json.loads(record['data'])
            db.execute('INSERT OR IGNORE INTO setting VALUES(?,?,?,?,?)',(number,row['id'],int(row['id'] in DEFAULTS),
                row['nome_pdf'],0))

    def add(self,number,name):
        number=cnpj(number); name=name.strip()
        if not name or len(name)>180: raise ValueError('Informe um nome de empresa com até 180 caracteres.')
        with self.connect() as db:
            if db.execute('SELECT 1 FROM company WHERE cnpj=?',(number,)).fetchone(): return False
            db.execute('INSERT INTO company VALUES(?,?)',(number,name)); self._ensure(db,number)
        return True

    def edit(self,old,number,name):
        number=cnpj(number); name=name.strip()
        if not name or len(name)>180: raise ValueError('Nome de empresa inválido.')
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM company WHERE cnpj=?',(old,)).fetchone(): raise ValueError('Empresa não encontrada.')
            if old!=number and db.execute('SELECT 1 FROM company WHERE cnpj=?',(number,)).fetchone(): raise ValueError('CNPJ já cadastrado.')
            db.execute('UPDATE company SET cnpj=?,name=? WHERE cnpj=?',(number,name,old))

    def delete(self,number):
        with self.connect() as db: db.execute('DELETE FROM company WHERE cnpj=?',(number,))

    def companies(self,query=''):
        with self.connect() as db: rows=[dict(r) for r in db.execute('SELECT cnpj,name FROM company ORDER BY name,cnpj')]
        q=query.casefold(); numeric=''.join(c for c in query if c.isdigit())
        return [r for r in rows if not q or q in r['name'].casefold() or (numeric and numeric in r['cnpj'])]

    def settings(self,number):
        with self.connect() as db:
            rows=db.execute('SELECT c.data,s.selected,s.filename,s.optional FROM catalog c JOIN setting s ON c.id=s.report WHERE s.company=? ORDER BY c.rowid',(number,)).fetchall()
        return [{**json.loads(r['data']),'selecionado':bool(r['selected']),'nome_pdf':r['filename'],
                 'opcional':False} for r in rows]

    def save_settings(self,number,rows):
        catalog={r['id']:r for r in self.catalog()}
        if {r['id'] for r in rows}!=set(catalog): raise ValueError('Configuração incompleta; recarregue a empresa.')
        # Nunca aceitar caminhos, regras especiais ou suporte alterados pela UI.
        merged=[{**catalog[r['id']],**{k:r[k] for k in ('selecionado','nome_pdf')},'opcional':False} for r in rows]
        validate_settings(merged)
        with self.connect() as db:
            for r in merged:
                db.execute('UPDATE setting SET selected=?,filename=?,optional=? WHERE company=? AND report=?',
                    (int(r['selecionado']),r['nome_pdf'],0,number,r['id']))

    def defaults(self,number):
        with self.connect() as db:
            db.execute('UPDATE setting SET selected=0 WHERE company=?',(number,))
            for id in DEFAULTS: db.execute('UPDATE setting SET selected=1 WHERE company=? AND report=?',(number,id))

    def preference(self,key,value=None):
        with self.connect() as db:
            if value is not None: db.execute('INSERT INTO preference VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value))
            row=db.execute('SELECT value FROM preference WHERE key=?',(key,)).fetchone()
            return row[0] if row else ''

    def backup(self,target):
        with self.connect() as source:
            dest=sqlite3.connect(target)
            try:source.backup(dest)
            finally:dest.close()

    def restore(self,source):
        source=Path(source)
        if source.resolve()==self.path.resolve():raise ValueError('Escolha outro arquivo de backup.')
        db=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
        try:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup inválido.')
            for number,name in db.execute('SELECT cnpj,name FROM company'):
                cnpj(number)
                if not isinstance(name,str) or not name.strip():raise ValueError('Cadastro inválido.')
            for table in ('catalog','setting','preference'):db.execute('SELECT * FROM '+table+' LIMIT 1')
            # Copia do cadastro atual antes de restaurar; nenhum PDF e tocado.
            from datetime import datetime
            backup=self.path.with_name('antes_restauracao_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.sqlite3')
            self.backup(backup)
            with self.connect() as dest:db.backup(dest)
        except sqlite3.Error:raise ValueError('Este arquivo não é um backup válido do programa.')
        finally:db.close()
        self.update_catalog(self.catalog())
        with self.connect() as dest:dest.execute('UPDATE setting SET optional=0')
