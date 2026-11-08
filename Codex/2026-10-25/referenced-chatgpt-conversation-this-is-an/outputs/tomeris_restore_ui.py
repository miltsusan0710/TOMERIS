import sys
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog
from tkinter.scrolledtext import ScrolledText

class RestorePanel:
    def __init__(self,app,path):
        self.app=app; self.path=path; self.checked=None; self.restored=None
        self.window=tk.Toplevel(app.root); self.window.title('バックアップの確認・別フォルダーへの復元')
        self.window.geometry('760x600'); self.window.minsize(600,500)
        self.window.transient(app.root); self.window.grab_set(); self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1); self.window.rowconfigure(1,weight=1)
        ttk.Label(self.window,text='バックアップの確認・復元',font=('Yu Gothic UI',16,'bold')).grid(row=0,column=0,sticky='w',padx=18,pady=14)
        self.body=ScrolledText(self.window,width=1,height=1,wrap='word',state='disabled',font=('Yu Gothic UI',11))
        self.body.grid(row=1,column=0,sticky='nsew',padx=18,pady=8)
        self.notice=tk.StringVar(value='バックアップを検査しています…')
        ttk.Label(self.window,textvariable=self.notice,wraplength=540).grid(row=2,column=0,sticky='ew',padx=18,pady=8)
        footer=ttk.Frame(self.window); footer.grid(row=3,column=0,sticky='ew',padx=18,pady=(0,14)); footer.columnconfigure(0,weight=1)
        self.restore_button=ttk.Button(footer,text='保存先を選んで別フォルダーに復元',command=self.restore)
        self.restore_button.grid(row=0,column=0,sticky='w')
        self.open_button=ttk.Button(footer,text='復元したデータで開く',command=self.open_restored)
        self.open_button.grid(row=1,column=0,sticky='w',pady=(8,0))
        self.exit_button=ttk.Button(footer,text='閉じる',command=self.close); self.exit_button.grid(row=1,column=1,sticky='e')
        self.run(lambda:app.service.inspect_backup(path),self.inspected,'バックアップを検査しています…'); self.state()
    def state(self):
        if not self.window.winfo_exists(): return
        active=not self.app.busy and not self.app.closing
        self.restore_button.configure(state='normal' if active and self.checked and not self.restored else 'disabled')
        self.open_button.configure(state='normal' if active and self.restored else 'disabled')
        self.exit_button.configure(state='normal' if active else 'disabled')
    def text(self,value):
        self.body.configure(state='normal'); self.body.delete('1.0','end'); self.body.insert('end',value); self.body.configure(state='disabled')
    def run(self,operation,callback,label):
        if self.app.busy or self.app.closing: return
        def work():
            try: result=(None,operation())
            except (OSError,ValueError) as exc: result=(str(exc),None)
            except Exception: result=('バックアップを処理できませんでした。',None)
            return completed,result
        def completed(result):
            if not self.window.winfo_exists(): return
            error,value=result
            if error: self.notice.set('処理を中止しました：'+error)
            else: callback(value)
            self.state()
        if self.app.submit('plan_result',work,label):
            self.notice.set(label); self.state()
    def inspected(self,value):
        self.checked=value; counts=value['counts']
        self.text(f"検査が完了しました。\n{self.path}\n\n作成日時：{value['created_at']}\n"
                  f"会話 {counts.get('conversations',0)}件 / 長期記憶 {counts.get('memories',0)}件 / 計画 {counts.get('plans',0)}件\n\n"
                  '含まれるデータ：\n'+'\n'.join(value['files'])+'\n\n'
                  '選んだ保存先の中に、新しい復元用フォルダーを作ります。今使っているデータは上書きしません。\n'
                  '復元後は別ウィンドウで確認できます。デスクトップのアイコンは引き続き元のデータを開きます。\n'
                  'Google接続情報・アプリ本体・AIモデル・人格／外部知識ファイルは復元対象外です。')
        self.notice.set('内容を確認して、復元先を選んでください。')
    def restore(self):
        if not self.checked or self.app.busy: return
        parent=filedialog.askdirectory(parent=self.window,title='新しい復元用フォルダーを置く場所を選ぶ',mustexist=True)
        if not parent: return
        digest=self.checked['digest']
        self.run(lambda:self.app.service.restore_backup(self.path,parent,digest),self.restored_ok,'別フォルダーに復元しています…')
    def restored_ok(self,folder):
        self.restored=folder
        self.text('復元が完了しました。\n'+folder+'\n\n今使っている記憶・計画は変更していません。\n'
                  '「復元したデータで開く」を押すと、このフォルダーを使う別ウィンドウを開きます。\n'
                  'そのウィンドウで保存した内容は復元フォルダーに保存されます。\n'
                  '通常のデスクトップアイコンは元のデータのままです。')
        self.notice.set('復元ファイルがバックアップの内容と一致することを確認しました。')
    def open_restored(self):
        if not self.restored or self.app.busy: return
        script=Path(__file__).with_name('tomeris_desktop.py')
        try:
            subprocess.Popen([sys.executable,'-B',str(script),'--data-dir',self.restored],cwd=str(script.parent))
        except OSError:
            self.notice.set('起動できませんでした。復元したファイルは保存されています。'); return
        self.notice.set('別ウィンドウの起動を要求しました。タイトルの「別データ」を確認してください。')
    def close(self):
        if self.app.busy:
            self.notice.set('処理が終わるまでお待ちください。'); return
        self.window.destroy()
