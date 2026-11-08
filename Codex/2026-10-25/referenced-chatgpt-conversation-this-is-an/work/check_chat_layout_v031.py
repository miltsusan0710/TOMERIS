from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v031'))
from tomeris_desktop_v0301 import TomerisWindow as PreviousWindow
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
for scale in (1.333333,2.666667):
    heights=[]
    for window_type in (PreviousWindow,TomerisWindow):
        with tempfile.TemporaryDirectory(dir='work/v07') as folder:
            root=tk.Tk();root.tk.call('tk','scaling',scale)
            app=window_type(root,data_dir=Path(folder),demo=True);wait(root,app)
            try:
                root.geometry('1120x850');root.update()
                for _ in range(10):root.update();time.sleep(.02)
                heights.append(app.transcript.winfo_height())
                if window_type is TomerisWindow:
                    assert not app.options_frame.winfo_ismapped()
                    bounds(root,[app.entry,app.send_button,app.transcript,app.copy_button,app.input_size_button])
                    width=app.transcript.winfo_width()
                    app.show_sidebar.set(False);app.update_chat_layout();root.update()
                    assert app.transcript.winfo_width()>width+150
                    app.show_chat_settings.set(True);app.update_chat_layout();root.update();assert app.mode_box.winfo_ismapped()
                    app.mode.set('2モデル比較');app.control_state();root.update();assert app.second_box.winfo_ismapped()
                    app.mode.set('会話＋自動検索');app.control_state()
                    app.show_chat_settings.set(False);app.update_chat_layout()
                    app.entry.insert('1.0','テスト入力');app.toggle_input_size();root.update()
                    assert int(app.entry['height'])==4 and app.entry.get('1.0','end-1c')=='テスト入力'
                    bounds(root,[app.entry,app.send_button,app.input_size_button]);app.toggle_input_size()
                    app.change_text_size(1);app.change_text_size(-1)
                    root.geometry('880x760');root.update()
                    bounds(root,[app.entry,app.send_button,app.transcript,app.copy_button]);assert app.transcript.winfo_height()>140
            finally:stop(root,app)
    assert heights[1]>heights[0]+40,heights
    print('Scale',scale,'conversation height:',heights[0],'->',heights[1],flush=True)
print('Chat layout, sidebar, settings, compare controls, input resize: OK')
