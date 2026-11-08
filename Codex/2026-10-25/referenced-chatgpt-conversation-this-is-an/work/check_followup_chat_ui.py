from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v029'))
import tomeris_search_methods as providers
import tomeris_evidence_v029 as evidence
from test_desktop_research_continuation import ROWS,page
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False
        with patch.object(providers,'wikipedia_search',return_value=ROWS),patch.object(evidence,'wikipedia_page',side_effect=page):
            app.entry.insert('1.0','アイアンマンについて調べて');app.send();wait(root,app)
            assert '資料1' in app.last_answer
            app.entry.delete('1.0','end');app.entry.insert('1.0','他の情報は？');app.send();wait(root,app)
            assert '資料3' in app.last_answer and '資料1' not in app.last_answer
    finally:stop(root,app)
print('Conversation UI: initial research -> follow-up -> new evidence OK')
