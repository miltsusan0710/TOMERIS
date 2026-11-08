from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v026'))
import tomeris_evidence_report as report
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False;app.service.model_names=[]
        def ask(text):
            app.entry.insert('1.0',text);app.send();wait(root,app);return app.last_answer
        with patch.object(report,'search_web',return_value=[]) as search:
            assert 'どの「ジャービス」' in ask('ジャービスに関するサイトを出して');search.assert_not_called()
            assert '本文根拠を取得できません' in ask('アイアンマン');assert search.called
        page=dict(title='Ollama',url='https://ollama.com/',published='',text='Ollama runs models locally on your computer. Ollama supports running and managing local models.')
        with patch.object(report,'fetch_page',return_value=page),patch.object(report,'search_web') as search:
            answer=ask('https://ollama.com/ を調べて');search.assert_not_called()
            assert '本文で確認した' in answer and 'https://ollama.com/' in answer
            assert any(t.startswith('url_') for t in app.transcript.tag_names())
        assert '結果：3' in ask('1+2')
    finally:stop(root,app)
print('Evidence UI: clarification, search failure, direct source report, links, arithmetic preserved: OK')
