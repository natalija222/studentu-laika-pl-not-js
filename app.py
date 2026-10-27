"""Studentu laika plānotājs — lokāls Tkinter/SQLite kursa prototips."""
import csv
import queue
import threading
import shutil
from pathlib import Path
from google_calendar import GoogleCalendar, validate_credentials
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta
from core import Store, free_slots

DAYS = ['Pirmdiena','Otrdiena','Trešdiena','Ceturtdiena','Piektdiena','Sestdiena','Svētdiena']


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Studentu laika plānotājs')
        self.geometry('1180x800')
        self.minsize(960, 690)
        self.configure(bg='#edf2f7')
        self.store = Store()
        self.slots = {}
        self.google = GoogleCalendar()
        self.google_queue = queue.Queue()
        self.google_busy = False
        self.credentials_path = Path(__file__).resolve().parent / "credentials.json"
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('TFrame', background='#edf2f7')
        style.configure('TLabel', background='#edf2f7', foreground='#172b4d')
        style.configure('Title.TLabel', font=('Segoe UI', 25, 'bold'))
        style.configure('Sub.TLabel', foreground='#526581')
        style.configure('TButton', padding=(12, 8))
        style.configure('Accent.TButton', background='#2563eb', foreground='white')
        style.map('Accent.TButton', background=[('active','#1d4ed8')])
        style.configure('Treeview', rowheight=33, background='white', fieldbackground='white')
        style.configure('Treeview.Heading', font=('Segoe UI',10,'bold'), padding=8)
        style.configure('TNotebook.Tab', padding=(22, 12))
        main = ttk.Frame(self, padding=24)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='Laiks tavām prioritātēm', style='Title.TLabel').pack(anchor='w')
        ttk.Label(main, text='Studentu laika plānotājs  /  lokāls prototips  /  dati saglabājas automātiski',
                  style='Sub.TLabel').pack(anchor='w', pady=(4,16))
        bar = ttk.Frame(main)
        bar.pack(fill='x', pady=(0,12))
        self.day = tk.StringVar(value=date.today().isoformat())
        self.period = tk.StringVar(value='Nedēļa')
        ttk.Label(bar,text='Datums (GGGG-MM-DD)').pack(side='left')
        ttk.Entry(bar,textvariable=self.day,width=13).pack(side='left',padx=8)
        ttk.Combobox(bar,textvariable=self.period,values=['Diena','Nedēļa'],state='readonly',width=10).pack(side='left')
        ttk.Button(bar,text='Atjaunot skatu',command=lambda:self.safe(self.refresh)).pack(side='left',padx=8)
        ttk.Button(bar,text='Ielādēt demo nedēļu',command=lambda:self.safe(self.demo)).pack(side='right')
        self.summary = ttk.Label(main,style='Sub.TLabel')
        self.summary.pack(anchor='w',pady=(0,12))
        self.tabs = ttk.Notebook(main)
        self.tabs.pack(fill='both',expand=True)
        self.calendar = self.tab('Kalendārs')
        self.free = self.tab('Brīvais laiks')
        self.tasks_tab = self.tab('Mācību uzdevumi')
        self.integrations = self.tab('Savienojumi')
        self.make_calendar()
        self.make_free()
        self.make_tasks()
        self.make_integrations()
        self.status = tk.StringVar(value='Gatavs. Sāc ar demo nedēļas ielādi vai pievieno savus notikumus.')
        ttk.Label(main,textvariable=self.status,style='Sub.TLabel',wraplength=1050).pack(anchor='w',pady=(12,0))
        self.refresh()

    def tab(self,title):
        frame=ttk.Frame(self.tabs,padding=16)
        self.tabs.add(frame,text=title)
        return frame

    def safe(self, action):
        try:
            action()
        except (ValueError,sqlite3.Error,OSError) as exc:
            messagebox.showerror('Neizdevās',str(exc),parent=self)

    def table(self,parent,columns):
        box=ttk.Frame(parent)
        box.pack(fill='both',expand=True,pady=10)
        tree=ttk.Treeview(box,columns=[c[0] for c in columns],show='headings',selectmode='browse')
        for key,title,width in columns:
            tree.heading(key,text=title)
            tree.column(key,width=width,minwidth=65)
        scroll=ttk.Scrollbar(box,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left',fill='both',expand=True)
        scroll.pack(side='right',fill='y')
        return tree

    def selected(self,tree):
        values=tree.selection()
        if not values:
            raise ValueError('Vispirms izvēlies rindu tabulā.')
        return values[0]

    def dates(self):
        d=date.fromisoformat(self.day.get())
        if self.period.get()=='Diena':
            return [d]
        monday=d-timedelta(days=d.weekday())
        return [monday+timedelta(days=i) for i in range(7)]

    def make_calendar(self):
        top=ttk.Frame(self.calendar)
        top.pack(fill='x')
        ttk.Label(top,text='Lekcijas, darbs, atpūta un ieplānotās mācības').pack(side='left')
        ttk.Button(top,text='+ Pievienot notikumu',style='Accent.TButton',command=self.event_dialog).pack(side='right')
        self.events_tree=self.table(self.calendar,[('title','Notikums',270),('start','Sākums',155),('end','Beigas',155),('kind','Veids',100),('source','Avots',100)])
        tools=ttk.Frame(self.calendar)
        tools.pack(fill='x')
        ttk.Button(tools,text='Dzēst izvēlēto',command=lambda:self.safe(self.remove_event)).pack(side='left')
        ttk.Button(tools,text='Eksportēt CSV',command=lambda:self.safe(self.export_csv)).pack(side='right')
        ttk.Label(self.calendar,text='Pārklājošies notikumi ir atļauti; aprēķinā tie tiek apvienoti. Visi laiki ir vietējie.',style='Sub.TLabel').pack(anchor='w',pady=8)

    def make_free(self):
        form=ttk.Frame(self.free)
        form.pack(fill='x')
        self.start=tk.StringVar(value='08:00')
        self.end=tk.StringVar(value='22:00')
        self.minimum=tk.StringVar(value='60')
        for title,var in [('Dienas sākums',self.start),('Dienas beigas',self.end),('Vismaz minūtes',self.minimum)]:
            ttk.Label(form,text=title).pack(side='left',padx=(0,5))
            ttk.Entry(form,textvariable=var,width=7).pack(side='left',padx=(0,16))
        ttk.Button(form,text='Atrast brīvo laiku',style='Accent.TButton',command=lambda:self.safe(self.calculate)).pack(side='right')
        self.free_info=ttk.Label(self.free,text='Aprēķins balstās uz saglabātajiem notikumiem.',style='Sub.TLabel')
        self.free_info.pack(anchor='w',pady=(12,0))
        self.free_tree=self.table(self.free,[('day','Diena',240),('start','No',90),('end','Līdz',90),('length','Ilgums (min)',100)])
        line=ttk.Frame(self.free)
        line.pack(fill='x')
        ttk.Label(line,text='Mācību uzdevums').pack(side='left')
        self.task_choice=ttk.Combobox(line,state='readonly',width=42)
        self.task_choice.pack(side='left',padx=8)
        ttk.Button(line,text='Ieplānot izvēlētajā laikā',style='Accent.TButton',command=lambda:self.safe(self.schedule)).pack(side='right')
        ttk.Label(self.free,text='Uzdevumu ievieto izvēlētā intervāla sākumā, ja tas ietilpst un nav nokavēts termiņš.',style='Sub.TLabel').pack(anchor='w',pady=8)

    def make_tasks(self):
        top=ttk.Frame(self.tasks_tab)
        top.pack(fill='x')
        ttk.Label(top,text='Darbi un termiņi, kuriem jāatrod laiks').pack(side='left')
        ttk.Button(top,text='+ Pievienot uzdevumu',style='Accent.TButton',command=self.task_dialog).pack(side='right')
        self.tasks_tree=self.table(self.tasks_tab,[('title','Uzdevums',280),('minutes','Minūtes',80),('deadline','Termiņš',110),('status','Statuss',110),('planned','Ieplānots',160)])
        line=ttk.Frame(self.tasks_tab)
        line.pack(fill='x')
        ttk.Button(line,text='Pabeigts / atjaunot',command=lambda:self.safe(self.toggle)).pack(side='left')
        ttk.Button(line,text='Dzēst uzdevumu',command=lambda:self.safe(self.remove_task)).pack(side='left',padx=8)
        ttk.Label(self.tasks_tab,text='Termiņš ir norādītās dienas beigas. Dzēšot uzdevumu, tiek dzēsts arī tā mācību notikums.',style='Sub.TLabel').pack(anchor='w',pady=8)

    def make_integrations(self):
        ttk.Label(self.integrations,text='Ārējo sistēmu savienojumi',font=('Segoe UI',17,'bold')).pack(anchor='w',pady=(0,14))
        ttk.Label(self.integrations,text='Google Calendar — galvenais kalendārs',font=('Segoe UI',12,'bold')).pack(anchor='w')
        ttk.Label(self.integrations,text='Ielādē izvēlētās dienas/nedēļas aizņemtos notikumus. Iepriekšējais Google imports tiek aizstāts.\nLaiki tiek pielāgoti datora laika joslai. Mācību plāni saglabājas tikai šajā lietotnē.',wraplength=900,style='Sub.TLabel').pack(anchor='w',pady=6)
        row=ttk.Frame(self.integrations)
        row.pack(fill='x')
        self.google_buttons=[]
        for label,callback in [('1. Izvēlēties Google JSON',self.select_credentials),('2. Savienot / atjaunot',self.sync_google),('Atvienot',self.disconnect_google)]:
            button=ttk.Button(row,text=label,command=lambda fn=callback:self.safe(fn))
            button.pack(side='left',padx=(0,8))
            self.google_buttons.append(button)
        self.google_status=tk.StringVar(value='Nav pieslēgts šajā sesijā. Vispirms sagatavo Google piekļuvi pēc GOOGLE_SETUP.md instrukcijas.')
        ttk.Label(self.integrations,textvariable=self.google_status,wraplength=900,style='Sub.TLabel').pack(anchor='w',pady=6)
        for title,description in [
            
            ('E-studijas — vēl nav pieslēgtas','Uzdevumus un termiņus šajā prototipā ievada manuāli sadaļā “Mācību uzdevumi”.'),
            ('SMS un e-pasts — vēl nav īstenoti','Prototips nesūta paziņojumus. Uzdevumu termiņi ir redzami uzdevumu sarakstā.')]:
            ttk.Label(self.integrations,text=title,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(12,4))
            ttk.Label(self.integrations,text=description,wraplength=850,style='Sub.TLabel').pack(anchor='w')
        ttk.Separator(self.integrations).pack(fill='x',pady=20)
        ttk.Label(self.integrations,text='Lokālie dati',font=('Segoe UI',12,'bold')).pack(anchor='w')
        ttk.Label(self.integrations,text='Šī ir viena lietotāja datora lietotne bez autorizācijas. Dati paliek šajā datorā.\nDatubāze: '+str(self.store.path),wraplength=850,style='Sub.TLabel').pack(anchor='w',pady=8)
        ttk.Button(self.integrations,text='Saglabāt datubāzes rezerves kopiju',command=lambda:self.safe(self.backup)).pack(anchor='w')

    def select_credentials(self):
        path=filedialog.askopenfilename(parent=self,title='Google Cloud Desktop app JSON',filetypes=[('JSON','*.json')])
        if not path:return
        validate_credentials(path)
        if Path(path).resolve()!=self.credentials_path.resolve():
            shutil.copyfile(path,self.credentials_path)
        self.google.disconnect()
        self.google_status.set('Piekļuves fails izvēlēts. Spied “Savienot / atjaunot”.')

    def sync_google(self):
        if self.google_busy:return
        days=self.dates()
        if not self.credentials_path.exists():
            raise ValueError('Vispirms izvēlies Google Cloud OAuth Desktop app JSON failu. Skati GOOGLE_SETUP.md.')
        self.google_busy=True
        for button in self.google_buttons:button.configure(state='disabled')
        self.google_status.set('Notiek pieslēgšanās / ielāde… Apstiprini piekļuvi atvērtajā Google pārlūka logā.')
        def work():
            try:
                events=self.google.fetch(self.credentials_path,days[0],days[-1])
                self.google_queue.put((True,events,days))
            except Exception as exc:
                self.google_queue.put((False,str(exc),days))
        threading.Thread(target=work,daemon=True).start()
        self.after(150,self.poll_google)

    def poll_google(self):
        try:ok,payload,days=self.google_queue.get_nowait()
        except queue.Empty:
            self.after(150,self.poll_google)
            return
        self.google_busy=False
        for button in self.google_buttons:button.configure(state='normal')
        if not ok:
            self.google_status.set('Ielāde neizdevās. Iepriekšējais imports saglabāts.')
            messagebox.showerror('Google Calendar',payload,parent=self)
            return
        try:
            self.store.replace_google(payload)
        except (ValueError,sqlite3.Error) as exc:
            self.google_status.set('Neizdevās saglabāt. Iepriekšējais imports saglabāts.')
            messagebox.showerror('Google Calendar',str(exc),parent=self)
            return
        self.day.set(days[0].isoformat())
        self.period.set('Diena' if len(days)==1 else 'Nedēļa')
        self.google_status.set(f'Ielādēti {len(payload)} aizņemti notikumi: {days[0]} – {days[-1]}. Atjaunots {datetime.now():%H:%M}.')
        self.safe(self.refresh)
        self.status.set('Google dati saglabāti. Brīvais laiks pārrēķināts. Pārslēdzot periodu, ielādē Google datus vēlreiz.')

    def disconnect_google(self):
        if not messagebox.askyesno('Atvienot Google?', 'Aizmirst pieslēgumu un izdzēst lokāli importētos Google notikumus? Google kalendārs netiks mainīts.',parent=self):return
        self.google.disconnect()
        self.store.replace_google([])
        self.google_status.set('Atvienots. Atļauju Google kontā var atsaukt myaccount.google.com/connections.')
        self.refresh()

    def refresh(self):
        days=self.dates()
        events=self.store.events()
        left=datetime.combine(days[0],datetime.min.time())
        right=datetime.combine(days[-1]+timedelta(days=1),datetime.min.time())
        visible=[e for e in events if datetime.fromisoformat(e['start'])<right and datetime.fromisoformat(e['end'])>left]
        self.events_tree.delete(*self.events_tree.get_children())
        for e in visible:
            self.events_tree.insert('', 'end',iid=str(e['id']),values=(e['title'],e['start'].replace('T',' '),e['end'].replace('T',' '),e['kind'],e['source']))
        tasks=self.store.tasks()
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        for t in tasks:
            state='Pabeigts' if t['done'] else ('Nokavēts' if t['deadline']<date.today().isoformat() else 'Jāizpilda')
            self.tasks_tree.insert('','end',iid=str(t['id']),values=(t['title'],t['minutes'],t['deadline'],state,(t['planned'] or '—').replace('T',' ')))
        self.task_map={f"{t['id']}. {t['title']} ({t['minutes']} min)":t['id'] for t in tasks if not t['done'] and not t['planned']}
        self.task_choice['values']=list(self.task_map)
        if self.task_choice.get() not in self.task_map:
            self.task_choice.set(next(iter(self.task_map),''))
        self.summary.configure(text=f"{days[0]:%d.%m.%Y} – {days[-1]:%d.%m.%Y}    •    {len(visible)} notikumi    •    {sum(not t['done'] for t in tasks)} nepabeigti uzdevumi")
        self.calculate()

    def calculate(self):
        slots=[]
        now=datetime.now().replace(second=0,microsecond=0)+timedelta(minutes=1)
        minimum=int(self.minimum.get())
        for day in self.dates():
            for a,b in free_slots(self.store.events(),day,self.start.get(),self.end.get(),minimum):
                a=max(a,now)
                if (b-a).total_seconds()>=minimum*60:
                    slots.append((a,b))
        self.free_tree.delete(*self.free_tree.get_children())
        self.slots={str(i):(a,b) for i,(a,b) in enumerate(slots)}
        for key,(a,b) in self.slots.items():
            self.free_tree.insert('','end',iid=key,values=(f'{DAYS[a.weekday()]}, {a:%d.%m.%Y}',f'{a:%H:%M}',f'{b:%H:%M}',int((b-a).total_seconds()/60)))
        total=sum(int((b-a).total_seconds()/60) for a,b in slots)
        self.free_info.configure(text=f'{len(slots)} piemēroti intervāli • {total//60} h {total%60} min pēc ilguma filtra. Pagājušie laiki netiek piedāvāti.')

    def dialog(self,title,fields,save):
        win=tk.Toplevel(self)
        win.title(title)
        win.transient(self)
        win.grab_set()
        frame=ttk.Frame(win,padding=22)
        frame.pack(fill='both',expand=True)
        variables={}
        for row,(key,label,default,choices) in enumerate(fields):
            ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',padx=(0,15),pady=7)
            var=tk.StringVar(value=default)
            variables[key]=var
            widget=ttk.Combobox(frame,textvariable=var,values=choices,state='readonly',width=30) if choices else ttk.Entry(frame,textvariable=var,width=33)
            widget.grid(row=row,column=1,sticky='ew',pady=7)
        def submit():
            def work():
                save({k:v.get() for k,v in variables.items()})
                win.destroy()
                self.refresh()
                self.status.set('Saglabāts datubāzē.')
            self.safe(work)
        ttk.Button(frame,text='Saglabāt',style='Accent.TButton',command=submit).grid(row=len(fields),column=1,sticky='e',pady=14)

    def event_dialog(self):
        d=self.day.get()
        self.dialog('Jauns notikums',[
            ('title','Nosaukums','',None),('day','Sākuma datums (GGGG-MM-DD)',d,None),
            ('start','Sākums (HH:MM)','09:00',None),('end_day','Beigu datums (GGGG-MM-DD)',d,None),
            ('end','Beigas (HH:MM)','10:00',None),('kind','Veids','Lekcija',['Lekcija','Darbs','Mācības','Atpūta','Cits'])],
            lambda v:self.store.add_event(v['title'],v['day']+'T'+v['start'],v['end_day']+'T'+v['end'],v['kind']))

    def task_dialog(self):
        self.dialog('Jauns mācību uzdevums',[
            ('title','Uzdevums','',None),('minutes','Nepieciešamās minūtes','60',None),
            ('deadline','Termiņš (GGGG-MM-DD)',(date.today()+timedelta(days=7)).isoformat(),None)],
            lambda v:self.store.add_task(v['title'],v['minutes'],v['deadline']))

    def demo(self):
        count=self.store.seed(date.fromisoformat(self.day.get()))
        self.refresh()
        self.status.set(f'Ielādēti {count} demo notikumi. Tie nav dati no Google Calendar.')

    def remove_event(self):
        key=self.selected(self.events_tree)
        if self.events_tree.item(key,'values')[-1]=='Google Calendar':
            raise ValueError('Google notikumu labo vai dzēs Google Calendar un pēc tam atjauno savienojumu.')
        if messagebox.askyesno('Dzēst notikumu?','Izvēlētais notikums tiks dzēsts no kalendāra.',parent=self):
            self.store.delete_event(int(key))
            self.refresh()

    def remove_task(self):
        key=self.selected(self.tasks_tree)
        if messagebox.askyesno('Dzēst uzdevumu?','Tiks dzēsts arī saistītais mācību notikums.',parent=self):
            self.store.delete_task(int(key))
            self.refresh()

    def toggle(self):
        self.store.toggle_task(int(self.selected(self.tasks_tree)))
        self.refresh()

    def schedule(self):
        a,b=self.slots[self.selected(self.free_tree)]
        task=self.task_map.get(self.task_choice.get())
        if task is None:
            raise ValueError('Vispirms pievieno vai izvēlies neieplānotu uzdevumu.')
        self.store.schedule(task,a.isoformat(),self.start.get(),self.end.get())
        self.refresh()
        self.status.set('Mācību laiks saglabāts kalendārā. Brīvie intervāli pārrēķināti.')

    def export_csv(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='kalendars.csv')
        if not path:return
        with open(path,'w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f,delimiter=';')
            writer.writerow(['Notikums','Sākums','Beigas','Veids','Avots'])
            for item in self.events_tree.get_children():
                values=self.events_tree.item(item,'values')
                writer.writerow(["'"+v if v.startswith(('=','+','-','@')) else v for v in values])
        self.status.set('Redzamā kalendāra dati eksportēti CSV failā.')

    def backup(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.db',filetypes=[('SQLite','*.db')],initialfile='planner_backup.db')
        if path:
            self.store.backup(path)
            self.status.set('Datubāzes rezerves kopija saglabāta.')


if __name__=='__main__':
    App().mainloop()
