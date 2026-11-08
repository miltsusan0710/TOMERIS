"""Selectable, resizable conversation cards on a scrollable canvas."""
import re
import tkinter as tk

class ChatCards(tk.Frame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,bg='#08131f')
        self.size=13;self.cards=[];self.pending=None;self.append_anchor=None
        self.columnconfigure(0,weight=1);self.rowconfigure(0,weight=1)
        self.canvas=tk.Canvas(self,bg='#08131f',highlightthickness=0)
        self.vbar=tk.Scrollbar(self,command=self.scroll)
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.grid(row=0,column=0,sticky='nsew');self.vbar.grid(row=0,column=1,sticky='ns')
        self.content=tk.Frame(self.canvas,bg='#08131f')
        self.window=self.canvas.create_window(0,0,anchor='nw',window=self.content)
        self.canvas.bind('<Configure>',self.resize)
        self.content.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<MouseWheel>',self.wheel)
    def set_font(self,size):
        self.size=size
        for _,body,_,_ in self.cards:body.configure(font=('Yu Gothic UI',size))
        self.resize()
    def scroll(self,*args):
        self.append_anchor=None
        self.canvas.yview(*args)
    def see(self,index):
        self.append_anchor=None
        self.update_idletasks();self.canvas.yview_moveto(1)
    def wheel(self,event):
        self.append_anchor=None
        self.canvas.yview_scroll(-int(event.delta/120),'units');return 'break'
    def resize(self,event=None):
        width=max(200,self.canvas.winfo_width())
        self.canvas.itemconfigure(self.window,width=width)
        for row,body,box,title in self.cards:
            box.configure(width=max(160,int(width*(.72 if title=='あなた' else .90))))
        if self.pending:self.after_cancel(self.pending)
        self.pending=self.after(40,self.measure)
    def measure(self):
        self.pending=None
        for _,body,_,_ in self.cards:
            count=int(body.tk.call(body._w,'count','-update','-displaylines','1.0','end'))
            body.configure(height=max(1,count))
        self.update_idletasks();self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        if self.append_anchor is not None:
            region=self.canvas.bbox('all')
            if region and region[3]>region[1]:
                self.canvas.yview_moveto((self.append_anchor-region[1])/(region[3]-region[1]))
            self.append_anchor=None
    def add(self,title,text,open_url):
        if self.append_anchor is None:self.append_anchor=self.canvas.canvasy(0)
        row=tk.Frame(self.content,bg='#08131f');row.pack(fill='x',padx=16,pady=(10,14))
        user=title=='あなた';color='#163b4a' if user else '#112337'
        box=tk.Frame(row,bg=color,highlightbackground='#286078' if user else '#214359',highlightthickness=1,width=400)
        box.pack(side='right' if user else 'left')
        box.grid_propagate(False)
        box.columnconfigure(0,weight=1)
        label=tk.Label(box,text=title,bg=color,fg='#80e5f5' if not user else '#c1f4fc',font=('Yu Gothic UI',10,'bold'),anchor='w')
        label.grid(row=0,column=0,sticky='ew',padx=16,pady=(10,0))
        body=tk.Text(box,width=1,height=1,wrap='word',font=('Yu Gothic UI',self.size),bg=color,fg='#e3eef7',relief='flat',borderwidth=0,padx=0,pady=0,spacing2=5,selectbackground='#326c85',selectforeground='white',cursor='xterm')
        body.grid(row=1,column=0,sticky='ew',padx=16,pady=(6,14));body.insert('1.0',text)
        for i,match in enumerate(re.finditer(r'https?://[^\s<>]+',text)):
            tag=f'url{i}';body.tag_add(tag,f'1.0+{match.start()}c',f'1.0+{match.end()}c');body.tag_configure(tag,foreground='#79dfff',underline=True)
            body.tag_bind(tag,'<Button-1>',lambda e,url=match.group():open_url(url))
        body.configure(state='disabled')
        for widget in (body,row,box,label):widget.bind('<MouseWheel>',self.wheel)
        def height(event):box.configure(height=label.winfo_reqheight()+body.winfo_reqheight()+32)
        body.bind('<Configure>',height)
        self.cards.append((row,body,box,title));self.resize()
