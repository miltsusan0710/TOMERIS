from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v022'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    try:
        before=app.service.memory_path.read_bytes()
        assert str(app.copy_button['state'])=='disabled'
        text='1. 通知を切る。\n2. 作業を始める。\n日本語・絵文字 🌱'
        app.append('トメリス',text); app.append('お知らせ','お知らせは対象外'); app.append('あなた','質問は対象外')
        with patch.object(root,'clipboard_clear') as clear,patch.object(root,'clipboard_append') as put:
            app.copy_button.invoke(); clear.assert_called_once(); put.assert_called_once_with(text)
        assert 'コピーしました' in app.status.get()
        with patch.object(root,'clipboard_clear',side_effect=tk.TclError('busy')):
            app.copy_button.invoke()
        assert 'コピーできません' in app.status.get() and app.last_answer==text
        app.busy=True; app.control_state()
        with patch.object(root,'clipboard_clear') as clear:
            app.copy_answer(); clear.assert_not_called()
        app.busy=False; app.control_state()
        app.append('トメリス','次の回答')
        with patch.object(root,'clipboard_clear'),patch.object(root,'clipboard_append') as put:
            app.copy_button.invoke(); put.assert_called_once_with('次の回答')
        for scale in (1.333333,2.666667):
            root.tk.call('tk','scaling',scale); root.geometry('860x600'); root.update()
            bounds(root,[app.copy_button])
        assert before==app.service.memory_path.read_bytes()
    finally: stop(root,app)
print('Copy UI: exact multiline text, latest reply, no question/notice, failure, busy guard, bounds, unchanged memory: OK (clipboard mocked)')
