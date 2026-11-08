from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v0301'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False
        with patch('tomeris_weather_service.fetch_weather',return_value='平塚市の明日の予報を取得しました。') as fetch:
            for question in ('明日の天気は？','現在地'):
                app.entry.delete('1.0','end');app.entry.insert('1.0',question);app.send();wait(root,app)
            assert '現在地は取得していません' in app.last_answer
            assert app.service.pending_weather=='明日';fetch.assert_not_called()
            app.entry.delete('1.0','end');app.entry.insert('1.0','平塚市');app.send();wait(root,app)
            fetch.assert_called_once_with('平塚市','明日');assert '平塚市の明日' in app.last_answer
    finally:stop(root,app)
print('Weather UI: tomorrow -> current location -> explicit city OK')
