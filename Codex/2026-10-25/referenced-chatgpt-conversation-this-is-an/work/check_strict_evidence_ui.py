from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v0261'))
import tomeris_evidence_report_v0261 as report
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False;app.service.model_names=['qwen2.5:3b']
        bad='韓国 シャインマスカット価格急落\n阪神ドラ3常深 珍しい名字に悩み\nマンガもお得にPayPayで ebookjapan'
        row=dict(title='Yahoo! JAPAN',snippet=bad,url='https://www.yahoo.co.jp/')
        with patch.object(report,'search_web',return_value=[row]),patch.object(report,'fetch_page',return_value=dict(row,text=bad,published='')),patch('tomeris_grounded_summary.LocalProvider') as model:
            app.entry.insert('1.0','アイアンマンについて調べて');app.send();wait(root,app)
            model.assert_not_called()
            assert '本文根拠を取得できません' in app.last_answer
            assert 'シャインマスカット' not in app.last_answer
            assert 'AI作成' not in app.last_answer
    finally:stop(root,app)
print('Exact reported failure reproduced in UI; unrelated source rejected, no generated claim: OK')
