from tkinter import filedialog,messagebox
from tomeris_learning_backup import create,inspect,restore

def open_learning_backup(app,restore_mode=False):
    if app.busy or app.closing or app.service is None:return
    def job(fn,done,label):app.submit('plan_result',lambda:(done,fn()),label)
    if not restore_mode:
        target=filedialog.asksaveasfilename(parent=app.root,title='取得経験・確認記録を保存',defaultextension='.zip',filetypes=[('ZIP','*.zip')])
        if target:job(lambda:create(app.service.data_dir,target),lambda text:app.append('お知らせ',text),'取得経験と確認記録を保存しています…')
        return
    path=filedialog.askopenfilename(parent=app.root,title='取得経験・確認記録のバックアップを選択',filetypes=[('ZIP','*.zip')])
    if not path:return
    def checked(value):
        if app.closing:return
        description='\n'.join(value['payload'])+'\n\n通常の記憶・計画は含みません。新しい別フォルダーへ復元します。現在のアプリには自動適用しません。'
        if not messagebox.askyesno('検査済みバックアップの復元',description,parent=app.root):return
        parent=filedialog.askdirectory(parent=app.root,title='復元フォルダーを作る場所')
        if parent:job(lambda:restore(path,parent,value['digest']),lambda text:app.append('お知らせ',text),'別フォルダーへ復元しています…')
    job(lambda:inspect(path),checked,'バックアップの形式と内容を検査しています…')
