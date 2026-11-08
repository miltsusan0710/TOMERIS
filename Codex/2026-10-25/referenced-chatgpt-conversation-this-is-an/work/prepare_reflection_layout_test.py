from pathlib import Path
p=Path('work/check_reflection_ui.py')
s=p.read_text(encoding='utf-8-sig').replace("'振り返り確認'","'振り返り確認'*20")
s=s.replace("root=tk.Tk(); root.withdraw();", "root=tk.Tk(); root.tk.call('tk','scaling',2.666667);")
s=s.replace('history.window.withdraw();','').replace('editor.window.withdraw();','')
s=s.replace("    editor.body.insert('1.0'", "    editor.window.geometry('580x440'); root.update()\n    for button in [editor.save_button,editor.exit_button]:\n        y=button.winfo_rooty()-editor.window.winfo_rooty()\n        assert y>=0 and y+button.winfo_height()<=editor.window.winfo_height()\n    assert editor.body.winfo_height()>1\n    editor.body.insert('1.0'",1)
Path('work/check_reflection_layout.py').write_text(s,encoding='utf-8')
