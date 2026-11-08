import sys,tempfile,json
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,'outputs')
import tkinter as tk
from tomeris_research_trials_ui import TrialPanel
from tomeris_research_trials import collect
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 root=tk.Tk();root.withdraw();app=Mock();app.root=root;app.busy=False;app.closing=False;app.service.demo=False;app.service.data_dir=Path(d)
 def submit(kind,work,label):
  done,result=work();done(result);return True
 app.submit=submit
 row=dict(title='情報検索',url='https://ja.wikipedia.org/wiki/test',wiki_id=1,wiki_lang='ja')
 page=dict(title='情報検索',url=row['url'],text='情報検索は、必要な情報を探し出すための方法として説明されています。',published='',updated='',provider='Wikipedia')
 with patch('tomeris_research_trials.wikipedia_search',return_value=[row]),patch('tomeris_research_trials.wikipedia_page',return_value=page):record=collect('情報検索','overview')
 panel=TrialPanel(app);panel.query.insert(0,'情報検索');root.update()
 with patch('tomeris_research_trials_ui.collect',return_value=record):panel.start()
 assert panel.path and panel.path.exists()
 assert '未採点' in panel.notice.get()
 assert panel.ratings['search_order'].get()=='未採点'
 assert '取得本文' in panel.body.get('1.0','end')
 panel.ratings['search_order'].set('適合');panel.ratings['exact_title_first'].set('適合');panel.reason.insert('1.0','テスト資料に対象の説明があることを確認。');panel.review()
 assert len(list((Path(d)/'research_trials').glob('*.review.*.json')))==1
 assert '未適用' in panel.notice.get()
 root.destroy()
 print('PASS: collection view, unreviewed state, explicit ratings, separate review file')
