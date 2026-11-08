import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

def open_review(app):
    if app.busy or app.closing or app.service is None:return
    win=tk.Toplevel(app.root);win.title('確認待ちの資料');win.geometry('800x650')
    tk.Label(win,text='疑いのある資料は参照候補へ取り込まず保留しています。\n検出は完全ではなく、批判・歴史的な引用も保留になる場合があります。').pack(pady=8)
    listing=tk.Listbox(win,height=7);listing.pack(fill='x',padx=12)
    body=ScrolledText(win,wrap='word',state='disabled');body.pack(fill='both',expand=True,padx=12,pady=8)
    ids=[]
    def reload():
        listing.delete(0,'end');ids.clear()
        for ident,row in app.service.catalogue.review_rows.items():
            if row['status']=='pending':
                ids.append(ident);listing.insert('end',row['item']['page']['title'])
        body.configure(state='normal');body.delete('1.0','end')
        body.insert('1.0',app.service.catalogue.review_error or ('資料を選んで内容を確認してください。' if ids else '確認待ちの資料はありません。'))
        body.configure(state='disabled')
    def select(event=None):
        if not listing.curselection():return
        row=app.service.catalogue.review_rows[ids[listing.curselection()[0]]];page=row['item']['page']
        body.configure(state='normal');body.delete('1.0','end')
        body.insert('1.0',page['title']+'\n'+page['url']+'\n\n保留理由：'+'、'.join(row['reasons'])+'\n\n【取得本文・外部資料】\n'+page['text'])
        body.configure(state='disabled')
    def decide(approved):
        if app.busy or app.closing or not listing.curselection():return
        ident=ids[listing.curselection()[0]]
        title='この内容を参照候補に許可' if approved else 'この内容を取り込まない'
        if not messagebox.askyesno(title,title+'設定にしますか？\n許可はこの資料の取得済み内容にだけ適用されます。',parent=win):return
        def done(message):
            app.append('お知らせ',message)
            if win.winfo_exists():reload()
        app.submit('plan_result',lambda:(done,app.service.catalogue.decide(ident,approved)),'資料の確認結果を保存しています…')
    listing.bind('<<ListboxSelect>>',select)
    bar=tk.Frame(win);bar.pack(pady=10)
    for title,fn in [('この内容を許可',lambda:decide(True)),('取り込まない',lambda:decide(False)),('後で確認',win.destroy)]:
        tk.Button(bar,text=title,command=fn).pack(side='left',padx=6)
    reload()
