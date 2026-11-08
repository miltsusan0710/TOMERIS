from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v030'))
import ctypes,subprocess
ctypes.windll.user32.SetProcessDPIAware()
for scale in (1.333333,2.666667):
    with tempfile.TemporaryDirectory(dir='work/v07') as folder:
        root=tk.Tk();root.tk.call('tk','scaling',scale)
        app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
        try:
            root.geometry('1120x850+30+30');root.update()
            app.append('あなた','アイアンマンについて調べて')
            app.append('トメリス','取得した資料を表示します。\n\nアイアンマンに関する本文と出典を確認できます。\n「他の情報は？」で追加の資料を調べます。')
            for _ in range(15):root.update();time.sleep(.03)
            bounds(root,[app.entry,app.send_button,app.transcript,app.mode_box,app.status_label])
            assert app.transcript.winfo_height()>140, (scale,app.transcript.winfo_height())
            app.change_text_size(1);app.change_text_size(-1)
            if scale==1.333333:
                x,y,w,h=root.winfo_rootx(),root.winfo_rooty(),root.winfo_width(),root.winfo_height()
                output=Path('outputs/tomeris_v030_preview.png').resolve()
                command=f"Add-Type -AssemblyName System.Drawing; $b=New-Object Drawing.Bitmap({w},{h}); $g=[Drawing.Graphics]::FromImage($b); $g.CopyFromScreen({x},{y},0,0,$b.Size); $b.Save('{output}',[Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $b.Dispose()"
                subprocess.run(['powershell','-NoProfile','-Command',command],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        finally:stop(root,app)
print('HUD layout and readable transcript at two DPI scales: OK')

