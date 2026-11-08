import sys,tempfile,shutil,json
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,'outputs')
import tkinter as tk
from test_desktop_trial_export import ExportTests
from tomeris_trial_dataset_ui import DatasetPanel
tempfile.tempdir=str(Path('work/v07').resolve())
fixture=ExportTests();fixture.setUp()
try:
 directory=fixture.root/'research_trials';directory.mkdir()
 for path in fixture.root.glob('*.json'):shutil.copyfile(path,directory/path.name)
 from tomeris_research_trials import digest
 for entry in fixture.manifest:
  p=directory/entry['record'];envelope=json.loads(p.read_text(encoding='utf-8'));envelope['record']['question']=envelope['record']['query'];envelope['sha256']=digest(envelope['record']);p.write_text(json.dumps(envelope),encoding='utf-8')
  p=directory/entry['review'];review=json.loads(p.read_text(encoding='utf-8'));review['record_sha256']=envelope['sha256'];p.write_text(json.dumps(review),encoding='utf-8')
 root=tk.Tk();root.withdraw();app=Mock();app.root=root;app.busy=False;app.closing=False;app.service.data_dir=fixture.root
 def submit(kind,work,label):
  done,result=work();done(result);return True
 app.submit=submit
 panel=DatasetPanel(app);root.update()
 assert len(panel.rows)==4 and not panel.selected
 for i,row in enumerate(panel.rows):
  panel.tree.selection_set(str(i));panel.show()
  panel.group.insert(0,'group'+str(i));panel.split.set('学習用' if i<2 else '評価用');panel.include()
 assert len(panel.selected)==4
 out=fixture.root/'exported.json';panel.write_to(out)
 assert out.exists() and len(json.loads(out.read_text(encoding='utf-8')))==4
 before=out.read_bytes();panel.write_to(out);assert '止めました' in panel.status.get();assert before==out.read_bytes()
 panel.tree.selection_set('2');panel.show();panel.group.delete(0,'end');panel.group.insert(0,'group0');panel.include()
 blocked=fixture.root/'blocked.json';panel.write_to(blocked);assert not blocked.exists();assert '跨' in panel.status.get()
 panel.exclude();assert len(panel.selected)==3
 root.destroy()
 print('PASS: initial no selection, explicit split, valid export, no overwrite, leakage blocked, remove selection')
finally:fixture.doCleanups()
