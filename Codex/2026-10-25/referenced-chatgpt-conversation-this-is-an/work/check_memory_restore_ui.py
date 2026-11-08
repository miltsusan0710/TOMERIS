from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v021'))

with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); root.tk.call('tk','scaling',2.666667)
    app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    try:
        app.service.remember('最初の目標','目標')
        app.view('memories'); wait(root,app); panel=app.memory_panel; panel.edit(); editor=panel.editor
        assert len(editor.versions)==1 and 'まだありません' in editor.message.get()
        editor.close(); panel.close()
        row=app.service.find_memories()['rows'][0]
        app.service.edit_memory(row['id'],row['_revision'],'現在の目標')
        before=app.service.memory_path.read_bytes()
        app.view('memories'); wait(root,app); panel=app.memory_panel; panel.edit(); editor=panel.editor
        editor.window.geometry('600x640'); root.update()
        bounds(editor.window,[editor.body,editor.version,editor.load_button,editor.save_button,editor.cancel_button])
        assert editor.body.winfo_height()>1
        editor.version.current(1); editor.stage()
        assert editor.body.get('1.0','end-1c')=='最初の目標'
        assert app.service.memory_path.read_bytes()==before
        editor.version.current(0)
        with patch('tomeris_memory_restore_ui.messagebox.askyesno',return_value=False): editor.stage()
        assert editor.body.get('1.0','end-1c')=='最初の目標'
        with patch('tomeris_memory_edit_ui.messagebox.askyesno',return_value=True): editor.close()
        assert app.service.memory_path.read_bytes()==before
        panel.edit(); editor=panel.editor; editor.version.current(1); editor.stage()
        with patch.object(app.service.store,'save',side_effect=OSError('保存失敗テスト')):
            editor.save(); wait(root,app)
        assert app.service.memory_path.read_bytes()==before
        assert editor.body.get('1.0','end-1c')=='最初の目標'
        editor.save(); wait(root,app)
        row=panel.result['rows'][0]
        assert row['text']=='最初の目標' and [v['text'] for v in row['edit_history']]==['最初の目標','現在の目標']
        panel.edit(); editor=panel.editor; assert len(editor.versions)==3
        editor.version.current(1); editor.stage()
        editor.body.insert('end','を調整')
        editor.version.current(2)
        with patch('tomeris_memory_restore_ui.messagebox.askyesno',return_value=True): editor.stage()
        assert editor.body.get('1.0','end-1c')=='最初の目標'
        editor.close(); panel.close()
    finally: stop(root,app)
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    try:
        app.view('memories'); wait(root,app); app.memory_panel.edit()
        assert app.memory_panel.editor.versions==['最初の目標','現在の目標','最初の目標']
        app.memory_panel.editor.close(); app.memory_panel.close()
    finally: stop(root,app)
print('Memory restore UI: history-free state, preview, cancel, dirty confirmation, failed save, retry, revision retention, restart, 200% layout: OK')
