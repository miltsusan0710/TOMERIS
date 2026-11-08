from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v028'))
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
import tomeris_methods_ui as ui
import tomeris_search_methods as methods
for scale in (1.333333,2.666667):
    with tempfile.TemporaryDirectory(dir='work/v07') as folder:
        root=tk.Tk();root.tk.call('tk','scaling',scale);app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
        try:
            app.open_methods();panel=app.methods_panel;root.update()
            panel.window.geometry('780x800');root.update()
            bounds(panel.window,[panel.google_button,panel.exit_button,panel.query])
            panel.tabs.select(panel.settings_tab);root.update();bounds(panel.window,[panel.mode_box,panel.save_button,panel.exit_button])
            panel.brave.insert(0,'BRAVE_TEST');panel.gemini.insert(0,'GEMINI_TEST');panel.mode.set('併用（Wikipedia＋Brave）');panel.save();wait(root,app)
            assert panel.brave.get()=='' and panel.gemini.get()==''
            assert app.service.methods.brave_key=='BRAVE_TEST'
            panel.query.insert(0,'アイアンマン')
            with patch.object(ui.webbrowser,'open',return_value=True) as browser:
                panel.open_browser('Google');assert browser.call_args.args[0].startswith('https://www.google.com/search?q=')
            row=dict(title='アイアンマン',url='https://ja.wikipedia.org/wiki/test',snippet='test')
            with patch.object(methods,'wikipedia_search',return_value=[row]),patch.object(methods,'brave_search',side_effect=methods.MethodError('テスト失敗')):
                panel.probe();wait(root,app);assert 'アイアンマン' in panel.detail.get('1.0','end')
            panel.tabs.select(panel.settings_tab);root.update();panel.clear();wait(root,app);assert app.service.methods.gemini_key=='' and app.service.methods.brave_key==''
            app.service.demo=False;panel.tabs.select(panel.search_tab);root.update();panel.google();wait(root,app);assert '未設定' in panel.message.get()
            panel.close()
            app.entry.insert('1.0','計算: 1+2');app.send();wait(root,app);assert '結果：3' in app.last_answer
        finally:stop(root,app)
print('Methods UI: ephemeral keys, browser handoff, partial provider failure, missing-key handling, layout, arithmetic: OK')
