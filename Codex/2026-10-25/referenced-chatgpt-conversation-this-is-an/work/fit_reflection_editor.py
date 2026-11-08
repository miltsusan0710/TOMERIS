from pathlib import Path
p=Path('outputs/tomeris_reflection_ui.py')
s=p.read_text(encoding='utf-8-sig').replace("geometry('700x520'); self.window.minsize(580,440)","geometry('700x560'); self.window.minsize(580,500)")
s=s.replace("len(value['goal'])<=100 else value['goal'][:100]", "len(value['goal'])<=40 else value['goal'][:40]")
p.write_text(s,encoding='utf-8')
