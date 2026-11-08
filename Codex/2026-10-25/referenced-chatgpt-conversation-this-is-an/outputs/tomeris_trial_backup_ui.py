"""Explicit backup/inspection dialogs, serialized with trial writes."""
import zipfile
from tomeris_trial_backup import backup,inspect

def open_backup(app,check=False):
    from tkinter import filedialog,messagebox
    if app.busy or app.closing:return
    if check:
        path=filedialog.askopenfilename(parent=app.root,title='比較記録バックアップを検査（展開しません）',filetypes=[('ZIP','*.zip')])
    else:
        path=filedialog.asksaveasfilename(parent=app.root,title='比較記録・採点のバックアップを新規保存',initialfile='research_trials_backup.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip')],confirmoverwrite=False)
    if not path:return
    def done(outcome):
        if app.closing:return
        result,error=outcome
        if error:
            messagebox.showerror('バックアップを完了できませんでした',error,parent=app.root);return
        title='バックアップ検査完了' if check else '比較記録のバックアップを保存しました'
        messagebox.showinfo(title,
            f"ファイル：{path}\n比較記録・採点：{len(result['files'])}ファイル\n保存時刻：{result['created_at']}\n\n"
            +'記憶・計画・学習データセット・実験結果は対象外です。\n'
            +'内容の正しさや採点の真偽を認定するものではありません。\n'
            +'元資料の変更、復元、学習結果の適用は行っていません。',parent=app.root)
    def work():
        try:
            result=inspect(path) if check else backup(app.service.data_dir/'research_trials',path)
            # Check fields used by the UI even when an archive is manually authored.
            if not isinstance(result.get('created_at'),str):raise ValueError('保存日時が不正です。')
            outcome=(result,None)
        except (OSError,ValueError,KeyError,TypeError,AttributeError,RuntimeError,zipfile.BadZipFile,NotImplementedError) as exc:
            outcome=(None,str(exc))
        return done,outcome
    app.submit('plan_result',work,'比較記録バックアップを検査しています…' if check else '比較記録と採点を別ZIPに保存しています…')
