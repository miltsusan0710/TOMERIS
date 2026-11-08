from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v025'))
import subprocess
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
for scale in (1.333333,2.666667):
    with tempfile.TemporaryDirectory(dir='work/v07') as folder:
        root=tk.Tk();root.tk.call('tk','scaling',scale)
        app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
        try:
            root.geometry('1120x850+50+40');root.lift();root.update()
            app.transcript.configure(state='normal');app.transcript.delete('1.0','end');app.transcript.configure(state='disabled')
            app.append('あなた','今日は何から始めればいい？')
            app.append('トメリス','まず、今日いちばん進めたいことを1つ選びましょう。\n\n1. やることを短い言葉で書く\n2. 最初の15分で取り組む内容を決める\n3. 通知を切って、その1つに集中する\n\nやりたいことを教えてくれれば、一緒に整理できます。')
            root.update();time.sleep(.15);root.update();app.transcript.see('1.0');root.update()
            assert app.orb.photo is not None
            if scale<2:
                root.attributes('-topmost',True);root.update();time.sleep(.2)
                dest=str(Path('outputs/tomeris_v025_preview.png').resolve())
                subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','work/capture_tomeris.ps1',str(root.winfo_rootx()),str(root.winfo_rooty()),str(root.winfo_width()),str(root.winfo_height()),dest],check=True)
                root.attributes('-topmost',False)
            for size in ('1120x850','880x760'):
                root.geometry(size);root.update()
                bounds(root,[app.entry,app.send_button,app.copy_button,app.mode_box,app.model_box,app.status_label])
                assert app.transcript.winfo_height()>60,(scale,size,app.transcript.winfo_height())
                for delta in (1,1,-1,-1):app.change_text_size(delta)
                root.update();assert app.chat_size==12
            app.mode.set('2モデル比較');app.control_state();root.update();assert app.second_box.winfo_ismapped()
            app.mode.set('会話＋自動検索');app.control_state();root.update();assert not app.second_box.winfo_ismapped()
            app.entry.insert('1.0','計算: 0.1+0.2');app.send();wait(root,app)
            assert '結果：0.3' in app.last_answer
            app.view('memories');wait(root,app);app.memory_panel.close()
        finally:stop(root,app)
print('Bright UI: orb, readable conversation, 100/200% sizes, input/button bounds, font controls, calculation, memory panel: OK')
