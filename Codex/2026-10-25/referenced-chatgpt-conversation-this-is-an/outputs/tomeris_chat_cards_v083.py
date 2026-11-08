"""One native text surface: no moving child windows or per-message measurement."""
import re
import tkinter as tk

class ChatCards(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#08131f', **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.body = tk.Text(self, wrap='word', state='disabled', font=('Yu Gothic UI', 13),
                            bg='#08131f', fg='#e3eef7', relief='flat', borderwidth=0,
                            highlightthickness=0, padx=18, pady=12, cursor='xterm',
                            selectbackground='#326c85', selectforeground='white')
        self.vbar = tk.Scrollbar(self, command=self.scroll)
        self.body.configure(yscrollcommand=self.vbar.set)
        self.body.grid(row=0, column=0, sticky='nsew')
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.body.tag_configure('assistant', background='#112337', lmargin1=14, lmargin2=14,
                                rmargin=40, spacing1=8, spacing2=4, spacing3=10)
        self.body.tag_configure('user', background='#163b4a', spacing1=8, spacing2=4, spacing3=10)
        self.body.tag_configure('heading', foreground='#80e5f5', font=('Yu Gothic UI', 11, 'bold'))
        self.body.tag_configure('gap', spacing1=8, spacing3=8)
        self.body.bind('<Configure>', self.resize)
        self.body.bind('<MouseWheel>', self.manual_scroll, add='+')
        self.body.bind('<Button-1>', self.manual_scroll, add='+')
        for key in ('<Prior>', '<Next>', '<Up>', '<Down>', '<Home>', '<End>'):
            self.body.bind(key, self.manual_scroll, add='+')
        self.pending = None
        self.serial = 0
        self.latest = None
        self.width = None

    def resize(self, event):
        if event.width == self.width:
            return
        self.width = event.width
        margin = max(18, int(event.width * .25))
        self.body.tag_configure('user', lmargin1=margin, lmargin2=margin, rmargin=14)

    def set_font(self, size):
        self.body.configure(font=('Yu Gothic UI', size))
        self.body.tag_configure('heading', font=('Yu Gothic UI', max(10, size-1), 'bold'))

    def manual_scroll(self, event=None):
        if self.pending is not None:
            self.after_cancel(self.pending)
            self.pending = None

    def scroll(self, *args):
        self.manual_scroll()
        self.body.yview(*args)

    def see(self, index):
        self.manual_scroll()
        # "Latest" means the beginning of the newest utterance, not its ending.
        self.body.yview(self.latest if index == 'end' and self.latest else index)

    def add(self, title, text, open_url):
        self.manual_scroll()
        self.serial += 1
        mark = f'message_{self.serial}'
        style = 'user' if title == 'あなた' else 'assistant'
        self.body.configure(state='normal')
        self.body.mark_set(mark, 'end-1c')
        self.body.mark_gravity(mark, 'left')
        self.body.insert('end', title+'\n', (style, 'heading'))
        start = self.body.index('end-1c')
        self.body.insert('end', text+'\n', (style,))
        for i, match in enumerate(re.finditer(r'https?://[^\s<>]+', text)):
            tag = f'url_{self.serial}_{i}'
            self.body.tag_add(tag, f'{start}+{match.start()}c', f'{start}+{match.end()}c')
            self.body.tag_configure(tag, foreground='#79dfff', underline=True)
            self.body.tag_bind(tag, '<Button-1>', lambda e, url=match.group(): open_url(url))
        self.body.insert('end', '\n', ('gap',))
        self.body.configure(state='disabled')
        self.latest = mark
        def reveal():
            self.pending = None
            self.body.yview(mark)
        self.pending = self.after_idle(reveal)

    def destroy(self):
        self.manual_scroll()
        super().destroy()
