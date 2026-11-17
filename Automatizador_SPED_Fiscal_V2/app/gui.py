import json
import os
from pathlib import Path
import queue
import threading
import time
from datetime import datetime
from uuid import uuid4
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk,filedialog,messagebox,simpledialog

from .branding import configure_taskbar,apply_icon,create_toplevel
from .catalog import BASE,load_catalog,discovered
from .domain import DEFAULTS,period,validate_settings,redact,format_competence
from .storage import Store
from .importers import HELP,import_companies


class Tooltip:
    def __init__(self,widget,text):
        self.widget=widget;self.text=text;self.window=None;self.timer=None
        widget.bind('<Enter>',self.enter);widget.bind('<Leave>',self.leave)
        widget.bind('<Destroy>',self.leave)
    def enter(self,event=None): self.timer=self.widget.after(450,self.show)
    def show(self):
        self.timer=None
        self.window=create_toplevel(self.widget);self.window.overrideredirect(True)
        self.window.geometry(f'+{self.widget.winfo_rootx()+20}+{self.widget.winfo_rooty()+20}')
        ttk.Label(self.window,text=self.text,justify='left',padding=12,relief='solid',wraplength=440).pack()
    def leave(self,event=None):
        if self.timer:self.widget.after_cancel(self.timer);self.timer=None
        if self.window:self.window.destroy();self.window=None


class App:
    def __init__(self,root,store=None):
        apply_icon(root)
        self.root=root;self.store=store or Store(BASE/'dados/empresas.sqlite3',load_catalog())
        self.messages=queue.Queue();self.stop=threading.Event();self.busy=False;self.started=None
        self.selected=set();self.statuses={};self.rows=[];self.current_company=None;self.editing_report=None;self.dirty=False
        self.cell_editor=None;self.cell_row=None;self.cell_iid=None
        self.execution_backend=None
        from .runtime import APP_VERSION
        root.title('Automatizador SPED Fiscal V2 · '+APP_VERSION)
        root.geometry(f'{max(980,min(1280,root.winfo_screenwidth()-60))}x{max(660,min(860,root.winfo_screenheight()-80))}')
        root.minsize(980,660)
        root.report_callback_exception=lambda *args:messagebox.showerror('Operação não concluída',
            'Verifique os dados e a disponibilidade da pasta de cadastro.',parent=root)
        style=ttk.Style(root)
        style.theme_use('clam')
        root.configure(background='#e1eaf5')
        for font in ('TkDefaultFont','TkTextFont'):tkfont.nametofont(font).configure(family='Segoe UI',size=10)
        style.configure('.',background='#e1eaf5',foreground='#243b59',font=('Segoe UI',10))
        style.configure('TNotebook',background='#e1eaf5',borderwidth=0)
        style.layout('TNotebook.Tab',[])
        style.configure('TNotebook.Tab',padding=(20,11),background='#e3eaf3')
        style.map('TNotebook.Tab',background=[('selected','#ffffff')],foreground=[('selected','#1557a0')])
        style.configure('TButton',padding=(12,7),background='#eaf0f8',bordercolor='#cfdae8')
        style.map('TButton',background=[('active','#dce9f8')])
        style.configure('Accent.TButton',background='#1b62b3',foreground='white',padding=(18,9))
        style.map('Accent.TButton',background=[('active','#164f91'),('disabled','#d4dce6')])
        style.configure('TEntry',padding=6,fieldbackground='white')
        style.configure('Treeview',rowheight=38,fieldbackground='#dce7f5',background='#dce7f5',borderwidth=0)
        style.configure('Treeview.Heading',padding=(12,12),background='#bfd2eb',foreground='#183b67',font=('Segoe UI',10,'bold'))
        style.map('Treeview',background=[('selected','#2868ad')],foreground=[('selected','#ffffff')])
        style.configure('Nav.TButton',background='#123358',foreground='#d5e4f7',padding=(18,15),anchor='w',borderwidth=0)
        style.map('Nav.TButton',background=[('active','#1b4777')])
        style.configure('ActiveNav.TButton',background='#2466a8',foreground='white',padding=(18,15),anchor='w',borderwidth=0)
        style.configure('Cell.TEntry',padding=3,fieldbackground='#ffffff',foreground='#153e6f')
        style.configure('Horizontal.TProgressbar',background='#2474c8',troughcolor='#e6edf5',borderwidth=0)
        header=tk.Frame(root,background='#143b67');header.pack(fill='x')
        tk.Label(header,text='AUTOMATIZADOR SPED FISCAL',font=('Segoe UI',17,'bold'),background='#143b67',foreground='white').pack(anchor='w',padx=25,pady=(16,2))
        tk.Label(header,text='Empresas, competência e relatórios em um só lugar · V'+APP_VERSION,font=('Segoe UI',10),background='#143b67',foreground='#c7dcf5').pack(anchor='w',padx=25,pady=(0,17))
        self.check_images={state:self.checkbox_image(state) for state in (False,True)}
        workspace=tk.Frame(root,background='#e1eaf5');workspace.pack(fill='both',expand=True)
        sidebar=tk.Frame(workspace,background='#123358',width=215);sidebar.pack(side='left',fill='y');sidebar.pack_propagate(False)
        tk.Label(sidebar,text='ÁREA DE TRABALHO',background='#123358',foreground='#90b1d9',font=('Segoe UI',9,'bold')).pack(anchor='w',padx=18,pady=(24,12))
        self.nav_buttons=[]
        for index,label in enumerate(['01   Processamento','02   Empresas','03   Relatórios']):
            button=ttk.Button(sidebar,text=label,style='Nav.TButton',command=lambda i=index:self.tabs.select(i))
            button.pack(fill='x',padx=9,pady=4);self.nav_buttons.append(button)
        tk.Label(sidebar,text='CONFIGURAÇÕES',background='#123358',foreground='#90b1d9',font=('Segoe UI',9,'bold')).pack(anchor='w',padx=18,pady=(30,8))
        for label,callback in [('Acesso ao PVA',self.environment_dialog),('Fazer backup',self.backup_data),('Restaurar cadastro',self.restore_data),('Código-fonte e licenças',self.open_sources)]:
            ttk.Button(sidebar,text=label,style='Nav.TButton',command=callback).pack(fill='x',padx=9,pady=2)
        tk.Label(sidebar,text='V2 · Windows\nDados salvos localmente',background='#123358',foreground='#90b1d9',justify='left',font=('Segoe UI',9)).pack(side='bottom',anchor='w',padx=18,pady=20)
        self.tabs=ttk.Notebook(workspace);self.tabs.pack(side='left',fill='both',expand=True,padx=18,pady=18)
        self.processing_tab=ttk.Frame(self.tabs,padding=12);self.company_tab=ttk.Frame(self.tabs,padding=12);self.report_tab=ttk.Frame(self.tabs,padding=12)
        for tab,title in [(self.processing_tab,'Processamento'),(self.company_tab,'Cadastro de Empresas'),(self.report_tab,'Configuração de Relatórios')]:self.tabs.add(tab,text=title)
        self.tabs.bind('<<NotebookTabChanged>>',self.nav_changed)
        self._processing();self._companies();self._reports();self.refresh()
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll)

    def checkbox_image(self,checked):
        image=tk.PhotoImage(master=self.root,width=20,height=20)
        border='#2468b5' if checked else '#8ba0b9'
        image.put(border,to=(1,1,19,19))
        image.put('#2468b5' if checked else '#ffffff',to=(2,2,18,18))
        if checked:
            for x,y in [(5,10),(6,11),(7,12),(8,13),(9,12),(10,11),(11,10),(12,9),(13,8),(14,7)]:
                image.put('#ffffff',to=(x,y,x+2,y+2))
        return image

    def nav_changed(self,event=None):
        current=self.tabs.index('current')
        for i,button in enumerate(self.nav_buttons):button.configure(style='ActiveNav.TButton' if current==i else 'Nav.TButton')

    def environment_dialog(self):
        if self.busy:return
        from .environment import check
        state=check()
        window=create_toplevel(self.root);window.title('Acesso ao PVA');window.transient(self.root)
        window.geometry('590x330');window.resizable(False,False)
        frame=ttk.Frame(window,padding=24);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Preparação do acesso ao PVA',font=('Segoe UI',16,'bold')).pack(anchor='w',pady=(0,15))
        text=('Componente Java: '+('encontrado' if state['ponte_encontrada'] else 'precisa ser preparado')+
              '\nComunicação Java: '+('habilitada' if state['acesso_habilitado'] else 'precisa ser habilitada'))
        ttk.Label(frame,text=text,justify='left').pack(anchor='w',pady=(0,15))
        ttk.Label(frame,text='O programa pode baixar o componente oficial necessário e preparar o acesso somente para seu usuário. Não substitui o Java do PVA. Se a comunicação for ativada agora, será necessário fechar e abrir o PVA uma vez.',wraplength=530,justify='left').pack(anchor='w',pady=(0,15))
        def prepare():
            window.destroy()
            from .environment import prepare as action
            self.background('ambiente',action)
        ttk.Button(frame,text='Preparar acesso automaticamente',style='Accent.TButton',command=prepare).pack(anchor='e')

    def backup_data(self):
        if self.busy:return
        path=filedialog.asksaveasfilename(parent=self.root,title='Salvar backup do cadastro',defaultextension='.sqlite3',filetypes=[('Cadastro SPED','*.sqlite3')])
        if path:
            try:self.store.backup(path);messagebox.showinfo('Backup','Backup salvo. Ele contém suas empresas e configurações.',parent=self.root)
            except Exception:messagebox.showerror('Backup','Não foi possível salvar o backup nesta pasta.',parent=self.root)

    def open_sources(self):
        from .runtime import RESOURCES
        folder=RESOURCES/'FONTES'
        if folder.is_dir():os.startfile(folder)
        else:messagebox.showinfo('Código-fonte','Os fontes deste projeto estão nesta pasta de desenvolvimento. Na distribuição EXE, acompanham o programa em FONTES.',parent=self.root)

    def restore_data(self):
        if self.busy:return
        path=filedialog.askopenfilename(parent=self.root,title='Restaurar cadastro',filetypes=[('Cadastro SPED','*.sqlite3')])
        if not path:return
        if not messagebox.askyesno('Restaurar cadastro','Substituir o cadastro atual pelo backup escolhido? Uma cópia do cadastro atual será preservada.',parent=self.root):return
        try:
            self.store.restore(Path(path).resolve());self.dirty=False;self.current_company=None;self.refresh()
            messagebox.showinfo('Cadastro','Cadastro e configurações restaurados.',parent=self.root)
        except ValueError as exc:messagebox.showerror('Cadastro',str(exc),parent=self.root)

    def offer_environment(self):
        from .environment import check
        if not check()['pronto']:self.environment_dialog()

    @staticmethod
    def checkbox_hit(tree,event):
        return (tree.identify_column(event.x)=='#0'
            and tree.identify_element(event.x,event.y).split('.')[-1]=='image')

    def format_month(self,event):
        value=self.competence.get();cursor=self.competence_entry.index('insert')
        numeric=sum(c.isdigit() for c in value[:cursor])
        formatted=format_competence(value,getattr(event,'keysym','') in {'BackSpace','Delete'})
        if formatted!=value:
            self.competence.set(formatted)
            self.competence_entry.icursor(min(len(formatted),numeric+(1 if numeric>=2 and '/' in formatted else 0)))

    def tree(self,parent,columns,headings,height=10):
        frame=ttk.Frame(parent);frame.pack(fill='both',expand=True,pady=6)
        tree=ttk.Treeview(frame,columns=columns,show='tree headings',height=height,selectmode='browse')
        tree.tag_configure('even',background='#e5edf8');tree.tag_configure('odd',background='#d3e1f2')
        tree.tag_configure('category',background='#bfd1e8',foreground='#214d7b',font=('Segoe UI',10,'bold'))
        tree.heading('#0',text='');tree.column('#0',width=50,stretch=False)
        for col,title in zip(columns,headings):tree.heading(col,text=title);tree.column(col,width=170)
        bar=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=bar.set)
        xbar=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview);tree.configure(xscrollcommand=xbar.set)
        tree.grid(row=0,column=0,sticky='nsew');bar.grid(row=0,column=1,sticky='ns');xbar.grid(row=1,column=0,sticky='ew')
        frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
        return tree

    def _processing(self):
        tab=self.processing_tab
        ttk.Label(tab,text='Deixe o PVA aberto. Em uma nova tentativa, a escrituração correta pode ser reutilizada.',wraplength=850).pack(anchor='w')
        buttons=ttk.Frame(tab);buttons.pack(fill='x',pady=6)
        ttk.Button(buttons,text='Selecionar todas',command=lambda:self.select_companies(True)).pack(side='left')
        ttk.Button(buttons,text='Desmarcar todas',command=lambda:self.select_companies(False)).pack(side='left',padx=6)
        self.process_tree=self.tree(tab,('name','cnpj','status'),('Empresa','CNPJ','Status'),8)
        self.process_tree.bind('<Button-1>',self.toggle_company)
        options=ttk.Frame(tab);options.pack(fill='x',pady=6)
        ttk.Label(options,text='Competência (MM/AAAA)').grid(row=0,column=0,sticky='w')
        self.competence=tk.StringVar(value=self.store.preference('competencia') or datetime.now().strftime('%m/%Y'))
        self.competence_entry=ttk.Entry(options,textvariable=self.competence,width=12);self.competence_entry.grid(row=1,column=0,sticky='w',padx=(0,15))
        self.competence_entry.bind('<KeyRelease>',self.format_month)
        ttk.Label(options,text='Pasta principal de destino').grid(row=0,column=1,sticky='w')
        self.destination=tk.StringVar(value=self.store.preference('destino'))
        self.dest_entry=ttk.Entry(options,textvariable=self.destination);self.dest_entry.grid(row=1,column=1,sticky='ew')
        self.browse=ttk.Button(options,text='Escolher…',command=self.choose_dest);self.browse.grid(row=1,column=2,padx=6)
        options.columnconfigure(1,weight=1)
        controls=ttk.Frame(tab);controls.pack(fill='x',pady=8)
        self.start_button=ttk.Button(controls,text='Iniciar processamento',style='Accent.TButton',command=self.start);self.start_button.pack(side='left')
        self.stop_button=ttk.Button(controls,text='Parar',command=self.request_stop,state='disabled');self.stop_button.pack(side='left',padx=8)
        self.elapsed=ttk.Label(controls,text='Tempo: 0 s');self.elapsed.pack(side='right')
        self.progress=ttk.Progressbar(tab,mode='determinate');self.progress.pack(fill='x')
        self.progress_text=tk.StringVar(value='Aguardando início.')
        ttk.Label(tab,textvariable=self.progress_text).pack(anchor='w',pady=5)
        self.output=tk.Text(tab,height=7,state='disabled',wrap='word',background='#f5f8fc',foreground='#30455e',relief='flat',padx=12,pady=10,font=('Consolas',10));self.output.pack(fill='both',expand=True)

    def _companies(self):
        search=ttk.Frame(self.company_tab);search.pack(fill='x',pady=(0,12))
        ttk.Label(search,text='Pesquisar nome ou CNPJ').pack(side='left')
        self.query=tk.StringVar();ttk.Entry(search,textvariable=self.query,width=38).pack(side='left',padx=8)
        self.query.trace_add('write',lambda *args:self.refresh_company_list())
        bar=ttk.Frame(self.company_tab);bar.pack(fill='x',pady=(0,8))
        for label,command in [('Cadastrar',lambda:self.company_form()),('Editar',self.edit_company),('Excluir',self.delete_company),('Importar Empresas',self.import_file)]:
            ttk.Button(bar,text=label,command=command).pack(side='left',padx=3)
        help_label=ttk.Label(bar,text='(?)',cursor='question_arrow');help_label.pack(side='left',padx=4)
        self.help=Tooltip(help_label,HELP)
        self.company_tree=self.tree(self.company_tab,('name','cnpj'),('Empresa','CNPJ'),15)
        ttk.Label(self.company_tab,text='O cadastro fica salvo neste computador. Novas empresas recebem os cinco relatórios padrão.').pack(anchor='w')

    def _reports(self):
        bar=ttk.Frame(self.report_tab);bar.pack(fill='x')
        ttk.Label(bar,text='Empresa').pack(side='left')
        self.company_choice=ttk.Combobox(bar,state='readonly',width=58);self.company_choice.pack(side='left',padx=8)
        self.company_choice.bind('<<ComboboxSelected>>',self.load_company)
        ttk.Button(bar,text='Atualizar árvore do PVA',command=self.update_catalog).pack(side='right')
        Tooltip(bar.winfo_children()[-1],'Busca novos relatórios na escrituração aberta. Não gera PDFs.\nPara o uso mensal normal, não é necessário atualizar.')
        actions=ttk.Frame(self.report_tab);actions.pack(fill='x',pady=8)
        ttk.Button(actions,text='Selecionar Padrão',command=self.set_default).pack(side='left')
        ttk.Button(actions,text='Salvar configurações',command=self.save_reports).pack(side='left',padx=8)
        self.report_tree=self.tree(self.report_tab,('pdf',),('Nome do PDF',),14)
        self.report_tree.heading('#0',text='Relatório no PVA',anchor='w')
        self.report_tree.column('#0',width=380,stretch=True);self.report_tree.column('pdf',width=370)
        self.report_tree.tag_configure('blocked',foreground='#8b97a8')
        self.report_tree.bind('<Button-1>',self.toggle_report)
        self.report_tree.bind('<Double-1>',self.edit_report)
        self.report_tree.bind('<Configure>',lambda event:self.cancel_inline())
        self.report_tree.bind('<MouseWheel>',lambda event:self.finish_inline())
        self.edit_hint=tk.StringVar(value='Duplo clique no nome do PDF para editar · Enter confirma · Esc cancela')
        ttk.Label(self.report_tab,textvariable=self.edit_hint,wraplength=800).pack(before=self.report_tree.master,anchor='w',pady=7)

    def info(self,text):
        self.output.configure(state='normal');self.output.insert('end',str(redact(text))+'\n');self.output.see('end');self.output.configure(state='disabled')

    def refresh_company_list(self):
        self.company_tree.delete(*self.company_tree.get_children())
        for i,r in enumerate(self.store.companies(self.query.get())): self.company_tree.insert('','end',iid=r['cnpj'],values=(r['name'],r['cnpj']),tags=('odd' if i%2 else 'even',))

    def refresh(self):
        companies=self.store.companies();self.selected.intersection_update(r['cnpj'] for r in companies)
        self.process_tree.delete(*self.process_tree.get_children())
        for i,r in enumerate(companies):self.process_tree.insert('','end',iid=r['cnpj'],image=self.check_images[r['cnpj'] in self.selected],values=(r['name'],r['cnpj'],self.statuses.get(r['cnpj'],'Aguardando')),tags=('odd' if i%2 else 'even',))
        self.refresh_company_list();self.choice_ids=[r['cnpj'] for r in companies]
        self.company_choice['values']=[r['name']+' — '+r['cnpj'] for r in companies]
        if self.current_company in self.choice_ids:self.company_choice.current(self.choice_ids.index(self.current_company))
        elif companies:self.company_choice.current(0);self.load_company()
        else:self.current_company=None;self.company_choice.set('');self.rows=[];self.draw_reports()

    def toggle_company(self,event):
        if self.busy or not self.checkbox_hit(self.process_tree,event):return
        id=self.process_tree.identify_row(event.y)
        if id:
            if id in self.selected:self.selected.remove(id)
            else:self.selected.add(id)
            self.process_tree.item(id,image=self.check_images[id in self.selected])

    def select_companies(self,selected):
        if self.busy:return
        self.selected=set(self.process_tree.get_children()) if selected else set();self.refresh()

    def company_form(self,old=None):
        if self.busy:return
        window=create_toplevel(self.root);window.title('Editar empresa' if old else 'Cadastrar empresa');window.transient(self.root);window.grab_set()
        frame=ttk.Frame(window,padding=18);frame.pack(fill='both',expand=True)
        number=tk.StringVar(value=old['cnpj'] if old else '');name=tk.StringVar(value=old['name'] if old else '')
        for i,(label,value) in enumerate([('CNPJ',number),('Nome da empresa',name)]):
            ttk.Label(frame,text=label).grid(row=i*2,column=0,sticky='w');ttk.Entry(frame,textvariable=value,width=55).grid(row=i*2+1,column=0,pady=(0,10))
        def save():
            try:
                if old:self.store.edit(old['cnpj'],number.get(),name.get())
                elif not self.store.add(number.get(),name.get()):raise ValueError('CNPJ já cadastrado; nada foi sobrescrito.')
                window.destroy();self.refresh()
            except ValueError as exc:messagebox.showerror('Cadastro',str(exc),parent=window)
        ttk.Button(frame,text='Salvar',command=save).grid(row=4,column=0,sticky='e')

    def edit_company(self):
        selection=self.company_tree.selection()
        if selection:
            self.company_form(next(r for r in self.store.companies() if r['cnpj']==selection[0]))

    def delete_company(self):
        if self.busy:return
        selected=self.company_tree.selection()
        if selected and messagebox.askyesno('Excluir empresa','Excluir o cadastro e suas configurações? Os PDFs serão preservados.',parent=self.root):
            self.store.delete(selected[0]);self.dirty=False;self.refresh()

    def import_file(self):
        if self.busy:return
        path=filedialog.askopenfilename(parent=self.root,title='Importar empresas sem cabeçalho',filetypes=[('Planilhas','*.csv *.xls *.xlsm')])
        if not path:return
        self.background('importacao',lambda:import_companies(path,self.store))

    def load_company(self,event=None):
        if not self.finish_inline():return
        index=self.company_choice.current()
        if index<0:return
        number=self.choice_ids[index]
        if self.dirty:
            if not messagebox.askyesno('Configuração','Descartar as alterações ainda não salvas da empresa anterior?',parent=self.root):
                if self.current_company in self.choice_ids:self.company_choice.current(self.choice_ids.index(self.current_company))
                return
        self.current_company=number;self.rows=self.store.settings(number);self.dirty=False;self.editing_report=None
        self.draw_reports()

    def draw_reports(self):
        self.cancel_inline()
        self.report_tree.delete(*self.report_tree.get_children());self.report_by_iid={};parents={}
        for index,row in enumerate(self.rows):
            parent=''
            for n in range(1,len(row['caminho_pva'])):
                key=tuple(row['caminho_pva'][:n])
                if key not in parents: parents[key]=self.report_tree.insert(parent,'end',text=key[-1],open=n<3,tags=('category',))
                parent=parents[key]
            supported=row.get('suporte')!='especial_nao_suportado'
            iid=self.report_tree.insert(parent,'end',text=row['caminho_pva'][-1],image=self.check_images[row['selecionado']],
                values=(row['nome_pdf'],),tags=(('odd' if index%2 else 'even'),) if supported else ('blocked',('odd' if index%2 else 'even')))
            self.report_by_iid[iid]=row

    def toggle_report(self,event):
        if self.busy or not self.checkbox_hit(self.report_tree,event):return
        iid=self.report_tree.identify_row(event.y);row=self.report_by_iid.get(iid)
        if row:
            if row.get('suporte')=='especial_nao_suportado':
                messagebox.showinfo('Relatório','Este item exige interação especial ainda não suportada.',parent=self.root);return
            row['selecionado']=not row['selecionado'];self.dirty=True
            self.report_tree.item(iid,image=self.check_images[row['selecionado']])

    def edit_report(self,event=None):
        if self.busy or event is None or self.report_tree.identify_column(event.x)!='#1':return
        if not self.finish_inline():return 'break'
        iid=self.report_tree.identify_row(event.y);row=self.report_by_iid.get(iid)
        box=self.report_tree.bbox(iid,'pdf') if row else ()
        if not box:return
        self.cell_iid=iid;self.cell_row=row
        editor=ttk.Entry(self.report_tree,style='Cell.TEntry',font=('Segoe UI',10))
        self.cell_editor=editor;editor.insert(0,row['nome_pdf'])
        editor.place(x=box[0],y=box[1],width=box[2],height=box[3]);editor.focus_set();editor.selection_range(0,'end')
        editor.bind('<Return>',lambda event:self.finish_inline());editor.bind('<Escape>',lambda event:self.cancel_inline())
        editor.bind('<FocusOut>',lambda event:self.finish_inline())
        return 'break'

    def finish_inline(self):
        if self.cell_editor is None:return True
        from .domain import filename
        value=self.cell_editor.get()
        try:
            filename(value)
            if self.cell_row['selecionado'] and any(r is not self.cell_row and r['selecionado'] and r['nome_pdf'].casefold()==value.casefold() for r in self.rows):
                raise ValueError('Já existe outro relatório selecionado com esse nome.')
        except ValueError as exc:self.edit_hint.set(str(exc));return False
        if value!=self.cell_row['nome_pdf']:
            self.cell_row['nome_pdf']=value;self.dirty=True
            self.report_tree.item(self.cell_iid,values=(value,))
        self.cancel_inline();self.edit_hint.set('Nome atualizado na tabela. Clique em Salvar configurações para manter a alteração.')
        return True

    def cancel_inline(self):
        editor=self.cell_editor;self.cell_editor=None;self.cell_row=None;self.cell_iid=None
        if editor is not None:editor.destroy()

    def set_default(self):
        if not self.finish_inline():return
        if not self.current_company:return
        for row in self.rows:row['selecionado']=row['id'] in DEFAULTS
        self.dirty=True;self.draw_reports()

    def save_reports(self):
        if not self.finish_inline():return
        if not self.current_company:return
        try:
            self.store.save_settings(self.current_company,self.rows);self.dirty=False
            messagebox.showinfo('Configurações','Configurações salvas somente para esta empresa.',parent=self.root)
        except ValueError as exc:messagebox.showerror('Configurações',str(exc),parent=self.root)

    def choose_dest(self):
        value=filedialog.askdirectory(parent=self.root,title='Pasta principal de destino')
        if value:self.destination.set(value)

    def update_catalog(self):
        if self.busy:return
        if self.dirty:
            messagebox.showinfo('Configurações','Salve as configurações antes de atualizar a árvore.',parent=self.root);return
        def job():
            if any((BASE/'logs'/name).exists() for name in ('automacao_ativa.lock','multiempresas_ativa.lock','empresa_unica_ativa.lock')):
                raise RuntimeError('automacao_ativa')
            from .pva import PVA
            paths=PVA().catalog(BASE/'logs'/('catalogo_'+uuid4().hex[:10]))
            rows=discovered(paths,self.store.catalog());self.store.update_catalog(rows)
            return len(rows)
        self.background('catalogo',job)

    def set_busy(self,value):
        self.busy=value
        for i in (1,2):self.tabs.tab(i,state='disabled' if value else 'normal')
        for i,button in enumerate(self.nav_buttons):button.configure(state='disabled' if value and i else 'normal')
        self.start_button.configure(state='disabled' if value else 'normal')
        self.competence_entry.configure(state='disabled' if value else 'normal')
        self.dest_entry.configure(state='disabled' if value else 'normal');self.browse.configure(state='disabled' if value else 'normal')

    def background(self,kind,fn):
        self.set_busy(True)
        def target():
            try:self.messages.put({'tipo':'tarefa','kind':kind,'resultado':fn()})
            except Exception as exc:
                from .errors import UserError
                text=str(exc) if isinstance(exc,UserError) else ('Não foi possível preparar o acesso. Verifique a conexão com a internet e tente novamente.' if kind=='ambiente' else 'Não foi possível concluir a tarefa. Verifique o arquivo e o estado do PVA.')
                self.messages.put({'tipo':'erro','texto':text})
        threading.Thread(target=target,daemon=True).start()

    def start(self):
        if self.busy:return
        if self.execution_backend is not None:
            pending=self.execution_backend.pending_workers()
            if pending:
                messagebox.showinfo('Aguarde os auxiliares','Ainda existe um auxiliar da execução anterior ativo. Nenhuma nova ação será iniciada até ele terminar.',parent=self.root)
                return
            from .locks import release_owned
            release_owned(BASE/'logs',os.getpid(),pending)
        if not self.finish_inline():return
        try:
            from .runtime import validate_resources
            validate_resources()
        except Exception:
            messagebox.showerror('Programa incompleto','Uma configuração do programa não foi encontrada. Abra a versão atualizada do executável. Nenhuma ação será feita no PVA.',parent=self.root)
            return
        from .environment import check
        if not check()['pronto']:
            self.environment_dialog();return
        if self.dirty:
            messagebox.showinfo('Configurações','Salve ou descarte as configurações pendentes antes de processar.',parent=self.root);return
        try:
            period(self.competence.get())
            if not self.destination.get().strip():raise ValueError('Escolha a pasta principal de destino.')
            jobs=[{**c,'relatorios':validate_settings(self.store.settings(c['cnpj']))} for c in self.store.companies() if c['cnpj'] in self.selected]
            if not jobs:raise ValueError('Selecione pelo menos uma empresa.')
            if any(not any(r['selecionado'] for r in j['relatorios']) for j in jobs):raise ValueError('Há empresa sem relatório selecionado.')
        except ValueError as exc:messagebox.showerror('Processamento',str(exc),parent=self.root);return
        competence=self.competence.get();destination=self.destination.get()
        self.store.preference('competencia',competence);self.store.preference('destino',destination)
        self.processing_ids=[j['cnpj'] for j in jobs];self.stop.clear();self.started=time.monotonic()
        self.set_busy(True);self.tabs.select(0);self.stop_button.configure(state='normal');self.progress['value']=0
        self.start_button.configure(text='Processando…')
        for id in self.processing_ids:self.statuses[id]='Aguardando'
        self.refresh();self.info('Início solicitado. Validando PVA vazio e destinos, sem sobrescritas.')
        def work():
            lock=BASE/'logs/multiempresas_ativa.lock';lock.parent.mkdir(exist_ok=True)
            common=BASE/'logs/automacao_ativa.lock'
            acquired=False;summary=None;common_acquired=False;backend=None;completion=None;run=None
            try:
                from .locks import recover_stale
                recover_stale(BASE/'logs')
                for other in ('empresa_unica_ativa.lock','execucao_ativa.lock','multiempresas_ativa.lock'):
                    if (BASE/'logs'/other).exists():raise RuntimeError('execucao_pendente')
                with common.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid()},f)
                common_acquired=True
                with lock.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid()},f)
                acquired=True
                from .processing import Processor
                from .pva import PVA
                run=BASE/'logs'/('multi_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid4().hex[:6])
                backend=PVA();self.execution_backend=backend
                summary=Processor(backend,self.messages.put,self.stop).run(jobs,competence,destination,run)
                completion={'tipo':'fim','resultado':summary,'resumos':str(run)}
            except Exception:completion={'tipo':'erro','texto':'Execução bloqueada: há outra execução ativa ou uma falha de configuração. Nenhuma nova ação foi repetida.'}
            finally:
                try:pending=backend.pending_workers() if backend is not None else []
                except Exception:pending=[0]
                released=False
                if acquired or common_acquired:
                    from .locks import release_owned
                    released=release_owned(BASE/'logs',os.getpid(),pending)
                if summary is not None:
                    summary['auxiliares_pendentes']=pending;summary['nova_tentativa_liberada']=released
                    from .processing import persist
                    try:persist(run,summary)
                    except Exception:completion={'tipo':'erro','texto':'Não foi possível atualizar o resumo. Verifique a permissão da pasta de registros; nenhum relatório será repetido automaticamente.'}
            # So habilitar a interface depois de encerrar a limpeza da execucao.
            if completion is not None:self.messages.put(completion)
        threading.Thread(target=work,daemon=False).start()

    def request_stop(self):
        if self.busy:
            self.stop.set();self.stop_button.configure(state='disabled');self.info('Parada solicitada. A operação de salvamento atual terminará antes da interrupção.')

    def poll(self):
        try:
            while True:self.handle(self.messages.get_nowait())
        except queue.Empty:pass
        if self.busy and self.started:self.elapsed.configure(text=f'Tempo: {time.monotonic()-self.started:.0f} s')
        self.root.after(100,self.poll)

    def handle(self,event):
        kind=event['tipo']
        if kind in {'empresa','relatorio','progresso'}:
            if 'total' in event:self.progress['maximum']=event['total'];self.progress['value']=event.get('feitos',0)
            if kind=='empresa':
                id=self.processing_ids[event['indice']];self.statuses[id]=event['status'];self.refresh()
                if 'empresa' in event:self.info('Empresa atual: '+event['empresa'])
            text=f"PDFs: {event.get('pdfs',0)} · Relatórios: {event.get('feitos',0)}/{event.get('total',0)}"
            if 'concluidas' in event:text+=f" · Empresas: {event['concluidas']}/{event['total_empresas']}"
            if 'relatorio' in event:text+=' · '+event['relatorio'];self.info(event['empresa']+' — '+event['relatorio'])
            self.progress_text.set(text)
        elif kind=='mensagem':self.info(event['texto'])
        elif kind=='fim':
            result=event['resultado'];self.set_busy(False);self.stop_button.configure(state='disabled')
            self.start_button.configure(text='Iniciar processamento' if result['sucesso'] else 'Tentar novamente')
            for id,row in zip(self.processing_ids,result['empresas']):self.statuses[id]=row['status']
            self.refresh();self.started=None
            text=f"PDFs: {result['pdfs']} · Tempo: {result['total_segundos']:.2f} s · "+('Concluído.' if result['sucesso'] else 'Interrompido ou com falhas.')
            self.progress_text.set(text);self.info(text);self.info('Resumos JSON/CSV: '+event['resumos'])
            if not result['sucesso']:
                if result.get('nova_tentativa_liberada'):self.info('Execução encerrada. Você pode corrigir a causa e tentar novamente sem fechar o programa.')
                elif result.get('auxiliares_pendentes'):self.info('Aguarde o auxiliar pendente terminar antes de iniciar novamente; nenhum processo será encerrado automaticamente.')
            messagebox.showinfo('Resumo',text,parent=self.root)
        elif kind=='tarefa':
            self.set_busy(False)
            if event['kind']=='ambiente':
                messagebox.showinfo('Acesso ao PVA',event['resultado']['texto'],parent=self.root)
            elif event['kind']=='importacao':
                r=event['resultado'];text=f"Importadas: {r['importadas']}\nJá existentes: {r['existentes']}\nRejeitadas: {r['rejeitadas']}"
                if r.get('erro_arquivo'):text+='\n'+r['erro_arquivo']
                text+='\n'+'\n'.join(f"Linha {x['linha']}: {x['motivo']}" for x in r['rejeicoes'])
                window=create_toplevel(self.root);window.title('Resultado da importação');window.geometry('650x430')
                box=tk.Text(window,wrap='word');box.pack(fill='both',expand=True,padx=12,pady=12);box.insert('end',text);box.configure(state='disabled')
            else:messagebox.showinfo('Catálogo',f"Catálogo atualizado: {event['resultado']} itens.",parent=self.root)
            self.refresh()
            if self.current_company:self.rows=self.store.settings(self.current_company);self.draw_reports()
        elif kind=='erro':
            self.set_busy(False);self.stop_button.configure(state='disabled')
            if self.started is not None:self.start_button.configure(text='Tentar novamente')
            self.started=None
            self.info(event['texto']);messagebox.showerror('Execução',event['texto'],parent=self.root)

    def close(self):
        if self.busy:
            if messagebox.askyesno('Processamento ativo','Solicitar parada segura? Aguarde a conclusão da operação atual antes de fechar.',parent=self.root):self.request_stop()
            return
        if self.execution_backend is not None and self.execution_backend.pending_workers():
            messagebox.showinfo('Auxiliar ativo','Ainda existe um auxiliar ativo. Aguarde sua conclusão antes de fechar o automatizador.',parent=self.root)
            return
        if self.dirty and not messagebox.askyesno('Configuração','Descartar configurações ainda não salvas e fechar?',parent=self.root):return
        self.root.destroy()


def main():
    configure_taskbar()
    root=tk.Tk()
    app=App(root);root.after(700,app.offer_environment);root.mainloop()
