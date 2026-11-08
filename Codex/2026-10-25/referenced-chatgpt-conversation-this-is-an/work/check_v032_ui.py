from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v032'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False
        with patch('tomeris_weather_service.fetch_weather',return_value='荒川区の明後日の予報') as fetch:
            for text in ('明日の荒川区の天気は？','明後日は？'):
                app.entry.delete('1.0','end');app.entry.insert('1.0',text);app.send();wait(root,app)
            assert fetch.call_args.args==('荒川区','明後日')
        app.entry.insert('1.0','今後は回答を短くして');app.send();wait(root,app)
        assert '会話の好みを覚えました' in app.last_answer
    finally:stop(root,app)
print('UI: day follow-up and explicit preference learning OK')
