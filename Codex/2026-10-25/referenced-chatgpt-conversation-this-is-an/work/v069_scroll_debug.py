import sys,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_chat_cards_v069 import ChatCards
root=tk.Tk();root.geometry('900x600');root.withdraw()
view=ChatCards(root);view.pack(fill='both',expand=True)
def settle():
 for _ in range(12):root.update();time.sleep(.02)
root.deiconify()
for i in range(12):view.add('トメリス',f'回答{i}\n'+('表示位置の検証です。\n'*5),lambda url:None)
settle()
for fraction in (0,.4,1):
 view.canvas.yview_moveto(fraction);settle();before=view.canvas.canvasy(0)
 view.add('トメリス','新しい長い回答\n'+('追加行です。\n'*25),lambda url:None);settle()
 after=view.canvas.canvasy(0)
 assert abs(after-before)<=1,(fraction,before,after)
 print('PASS: reply preserves pixel position',fraction,before,after)
view.add('あなた','次の質問',lambda url:None);settle()
print('user',after,view.canvas.canvasy(0),view.canvas.bbox('all'));print([(b.cget('height'),box.winfo_height()) for _,b,box,_ in view.cards]);assert abs(view.canvas.canvasy(0)-after)<=1
view.see('end');settle();assert view.canvas.yview()[1]>=.999
print('PASS: user message preserves position; Latest button moves to end')
root.destroy()

