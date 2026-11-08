from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v024'))
import tomeris_web_search as web
import tomeris_capabilities as cap
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        assert app.mode.get()=='会話＋自動検索'
        app.service.demo=False; app.service.model_names=[]
        def ask(question):
            app.entry.insert('1.0',question);app.send();wait(root,app);return app.last_answer
        selftest=ask('計算: (1200 + 800) * 1.1');assert '結果：2200' in selftest
        with patch.object(web,'search_web',return_value=[]) as search:
            assert '地域名だけ' in ask('今日の天気は？')
            assert '荒川区の今日の天気' in ask('荒川区')
            search.assert_called_once_with('荒川区の今日の天気')
        rows=[dict(title='Ollama',url='https://ollama.com/',snippet='Run local models')]
        with patch.object(cap,'search_web',return_value=rows) as search:
            answer=ask('調査: Ollama');assert '収集した出典' in answer;assert search.call_count==3
        app.mode.set('情報収集');app.control_state();assert str(app.memory_check['state'])=='disabled'
        with patch.object(cap,'search_web',return_value=rows):assert '確認の範囲' in ask('Ollama')
        app.mode.set('会話');app.control_state();app.service.model_names=['qwen2.5:3b']
        app.service.session_turns=[]
        with patch.object(cap,'LocalProvider') as provider:
            provider.return_value.generate.return_value='短く話します。'
            ask('短く説明してほしい')
            ask('その話し方で続けて')
            assert '短く説明してほしい' in str(provider.return_value.generate.call_args)
        assert not app.busy
        root.update();bounds(root,[app.mode_box,app.send_button,app.copy_button])
    finally:stop(root,app)
print('v0.24 UI: weather followup, exact arithmetic, research auto/manual, conversation context, controls: OK')
