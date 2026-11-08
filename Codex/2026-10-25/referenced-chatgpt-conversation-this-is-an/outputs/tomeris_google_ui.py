"""Google connection UI. All network and disk work uses the app's worker."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import webbrowser
from tomeris_google import GoogleError

class GooglePanel:
    def __init__(self,app):
        self.app=app; self.api=app.service.google; self.accounts=[]
        self.window=tk.Toplevel(app.root)
        self.window.title('Googleカレンダー（読み取り専用）')
        self.window.geometry('820x650'); self.window.minsize(700,530)
        self.window.transient(app.root); self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.message=tk.StringVar(value='接続情報を確認しています…')
        ttk.Label(self.window,text='Googleカレンダー',font=('Yu Gothic UI',18,'bold')).pack(anchor='w',padx=18,pady=(16,6))
        ttk.Label(self.window,text='予定の閲覧のみ。取得した予定は会話履歴に保存せず、AIにも送りません。',wraplength=750).pack(anchor='w',padx=18)
        setup=ttk.Frame(self.window); setup.pack(fill='x',padx=18,pady=12)
        help_button=ttk.Button(setup,text='初回設定の手順',command=self.help)
        help_button.pack(side='left')
        config=ttk.Button(setup,text='設定JSONを選ぶ',command=self.configure); config.pack(side='left',padx=8)
        add=ttk.Button(setup,text='アカウントを追加／再接続',command=self.connect); add.pack(side='left')
        row=ttk.Frame(self.window); row.pack(fill='x',padx=18,pady=6)
        self.choice=ttk.Combobox(row,values=['すべてのアカウント'],state='readonly',width=38)
        self.choice.current(0); self.choice.pack(side='left',fill='x',expand=True)
        fetch=ttk.Button(row,text='今日の予定を取得',command=self.fetch); fetch.pack(side='left',padx=8)
        remove=ttk.Button(row,text='登録を削除',command=self.forget); remove.pack(side='left')
        self.output=ScrolledText(self.window,wrap='word',font=('Yu Gothic UI',11),state='disabled',height=16)
        self.output.pack(fill='both',expand=True,padx=18,pady=12)
        ttk.Label(self.window,textvariable=self.message,wraplength=760).pack(anchor='w',padx=18,pady=6)
        footer=ttk.Frame(self.window); footer.pack(fill='x',padx=18,pady=(0,12))
        ttk.Button(footer,text='処理を中止',command=self.cancel).pack(side='left')
        ttk.Button(footer,text='閉じる',command=self.close).pack(side='right')
        self.controls=[config,add,fetch,remove]
        self.run(self.api.status,self.show_status,'接続情報を確認しています…')
        self.state()
    def state(self):
        if not self.window.winfo_exists():
            return
        active=not self.app.busy and not self.app.closing
        for item in self.controls:
            item.configure(state='normal' if active else 'disabled')
        self.choice.configure(state='readonly' if active else 'disabled')
    def show_text(self,text):
        self.output.configure(state='normal'); self.output.delete('1.0','end')
        self.output.insert('end',text); self.output.configure(state='disabled')
    def run(self,operation,callback,label):
        if self.app.busy or self.app.closing:
            return
        self.api.cancel.clear()
        def work():
            try:
                result=(None,operation())
            except GoogleError as exc:
                result=(str(exc),None)
            except OSError:
                result=('接続情報の読込・保存または通信に失敗しました。',None)
            except Exception:
                result=('処理を完了できませんでした。接続設定やGoogleの応答を確認してください。',None)
            return complete,result
        def complete(result):
            if not self.window.winfo_exists():
                return
            error,value=result
            if error:
                self.message.set(error)
            else:
                callback(value)
            self.state()
        if self.app.submit('plan_result',work,label):
            self.message.set(label); self.state()
    def show_status(self,status):
        self.accounts=status['accounts']
        self.choice.configure(values=['すべてのアカウント']+[a['email'] for a in self.accounts])
        self.choice.current(0)
        self.message.set(('設定済み' if status['configured'] else '初回設定が必要です。「初回設定の手順」を開いてください。')+f" / 登録 {len(self.accounts)}アカウント")
        self.show_text('アカウントを追加すると、ここで今日の予定を確認できます。\n「今日の予定を取得」を押したときにGoogleへ接続します。')
    def help(self):
        path=Path(__file__).with_name('Googleカレンダー初回設定.html')
        webbrowser.open(path.resolve().as_uri())
    def configure(self):
        path=filedialog.askopenfilename(parent=self.window,title='Googleのデスクトップアプリ認証JSONを選択',filetypes=[('JSON','*.json')])
        if path:
            self.run(lambda:self.api.configure(path),self.show_status,'認証設定をWindowsで保護して保存しています…')
    def connect(self):
        self.run(self.api.connect,self.show_status,'ブラウザーで接続するアカウントと読み取り権限を確認してください（待機は最大3分）。')
    def selected(self):
        index=self.choice.current()-1
        return self.accounts[index]['id'] if 0<=index<len(self.accounts) else None
    def fetch(self):
        account=self.selected()
        def show(text):
            self.show_text(text); self.message.set('取得処理が終了しました。取得できなかった場合も画面内に表示します。')
        self.run(lambda:self.api.agenda(account),show,'Googleから今日の予定を読み込んでいます…')
    def forget(self):
        account=self.selected()
        if not account:
            self.message.set('削除するアカウントを一覧から1つ選んでください。'); return
        if messagebox.askyesno('このアプリから登録を削除',self.choice.get()+'\n\nこのPCに保存した接続情報を削除します。Google上の予定は削除しません。\nGoogle側の許可も取り消す場合はGoogleアカウントの「サードパーティとの接続」から操作してください。',parent=self.window):
            self.run(lambda:self.api.forget(account),self.show_status,'登録を削除しています…')
    def cancel(self):
        self.api.cancel.set()
        if self.app.busy:
            self.message.set('中止を要求しました。通信中の場合は応答またはタイムアウトまでお待ちください。')
    def close(self):
        if self.app.busy:
            self.cancel(); return
        self.window.destroy()
