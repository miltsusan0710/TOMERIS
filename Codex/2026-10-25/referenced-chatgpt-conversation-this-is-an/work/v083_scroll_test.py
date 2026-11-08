import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'outputs'))
import tkinter as tk
from tomeris_chat_cards_v083 import ChatCards

root = tk.Tk()
root.geometry('900x600')
view = ChatCards(root)
view.pack(fill='both', expand=True)
try:
    root.update()
    for i in range(60):
        view.add('あなた' if i % 2 else 'トメリス', f'発言{i}\n'+('長い会話の確認です。'*10+'\n')*8, lambda url: None)
    root.update()
    assert len(view.winfo_children()) == 2  # constant widget count despite history
    view.add('トメリス', '回答の最初の文です。\n'+('続きです。\n'*100)+'https://example.org/', lambda url: None)
    root.update()
    assert view.body.dlineinfo(view.latest) is not None
    assert view.body.dlineinfo(f'{view.latest}+1line') is not None
    assert view.body.compare(view.body.index('@0,0'), '<=', f'{view.latest}+1line')
    ranges = view.body.tag_ranges('url_61_0')
    assert view.body.get(*ranges) == 'https://example.org/'
    assert view.body.cget('state') == 'disabled'
    start = time.perf_counter()
    for i in range(100):
        view.scroll('scroll', -1 if i < 50 else 1, 'units')
        root.update_idletasks()
    print(f'100 scroll redraws: {time.perf_counter()-start:.3f}s')
    view.add('トメリス', '次の回答\n'+('内容\n'*100), lambda url: None)
    view.scroll('moveto', 0)
    root.update()
    assert view.body.yview()[0] == 0  # manual movement cancels queued jump
    view.see('end'); root.update()
    assert view.body.dlineinfo(view.latest) is not None
    view.set_font(18); root.geometry('500x450'); root.update()
    view.see('end'); root.update()
    assert view.body.dlineinfo(f'{view.latest}+1line') is not None
    view.add('あなた', '終了直前', lambda url: None)
    view.destroy(); root.update()
    print('PASS: first sentence, manual override, links, resize, font, constant widgets, pending cleanup')
finally:
    root.destroy()
