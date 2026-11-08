from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v0231'))
import tomeris_web_search as web
import tomeris_desktop_v0231 as ui
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    try:
        assert app.mode.get()=='会話＋自動検索'
        app.entry.insert('1.0','今日の天気は？'); app.send(); wait(root,app)
        assert '市区町村' in app.last_answer
        before=app.service.memory_path.read_bytes()
        app.entry.insert('1.0','今日の作業に集中する工夫は？'); app.send(); wait(root,app)
        assert '画面確認用の応答' in app.last_answer
        with patch.object(web,'search_web') as search:
            app.entry.insert('1.0','最新のOllamaを調べて'); app.send(); wait(root,app)
            assert '画面確認用の検索結果' in app.last_answer
        app.mode.set('ネット検索'); app.control_state(); assert str(app.memory_check['state'])=='disabled'
        app.service.demo=False; app.service.model_names=[]
        rows=[dict(title='Ollama',snippet='Run local models',url='https://ollama.com/')]
        with patch.object(web,'search_web',return_value=rows) as search:
            app.entry.insert('1.0','Ollama'); app.send(); wait(root,app); search.assert_called_once_with('Ollama')
        assert 'https://ollama.com/' in app.last_answer and '全文は未取得' in app.last_answer
        tags=[t for t in app.transcript.tag_names() if t.startswith('url_')]
        assert tags
        ranges=app.transcript.tag_ranges(tags[-1]); assert app.transcript.get(*ranges)=='https://ollama.com/'
        with patch.object(ui.webbrowser,'open',return_value=True) as opened:
            app.open_source('https://ollama.com/'); opened.assert_called_once_with('https://ollama.com/')
            app.open_source('file:///C:/'); assert opened.call_count==1
        with patch.object(web,'search_web',side_effect=web.SearchError('通信失敗')):
            app.entry.insert('1.0','Ollama'); app.send(); wait(root,app)
        assert '回答は作っていません' in app.last_answer
        assert not app.busy
    finally: stop(root,app)
print('Default auto-search UI: mode routing, missing location, offline summary fallback, source links, network error recovery: OK')
