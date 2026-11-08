from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v0251'))
import tomeris_site_search as sites
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False;app.service.model_names=[]
        row=dict(title='ジャービスについて',url='https://example.com/jarvis',snippet='ジャービスの紹介')
        with patch.object(sites,'search_web',return_value=[row,row]) as search:
            app.entry.insert('1.0','ジャービスに関するサイトを出して');app.send();wait(root,app)
            search.assert_called_once_with('ジャービス')
            assert app.last_answer.count(row['url'])==1
            assert any(t.startswith('url_') for t in app.transcript.tag_names())
        with patch.object(sites,'search_web',return_value=[]):
            app.entry.insert('1.0','ジャービスのサイトを出して');app.send();wait(root,app)
            assert '未確認のURLは作りません' in app.last_answer
    finally:stop(root,app)
print('Site UI: exact user prompt routes to retrieval, no model needed, deduplication, clickable link, empty result: OK')
