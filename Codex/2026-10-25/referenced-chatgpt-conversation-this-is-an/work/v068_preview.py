import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v068 import TomerisWindow
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 root=tk.Tk();app=TomerisWindow(root,Path(d),True)
 def seed():
  app.append('あなた','今日の作業に集中するための工夫を教えて。')
  app.append('トメリス','まずは、取り組む作業を一つに絞りましょう。\n\n1. 通知を切り、必要な資料だけを開く。\n2. 25分だけ作業し、短い休憩を取る。\n3. 終わったところを記録して、次の一歩を決める。\n\n画像や音声も、下のボタンから使えます。')
 root.after(1200,seed);root.after(180000,app.close);root.mainloop()
