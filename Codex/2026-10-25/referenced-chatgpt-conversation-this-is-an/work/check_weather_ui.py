from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v0241'))
import tomeris_weather_service as weather
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
    try:
        app.service.demo=False;app.service.model_names=[]
        def ask(text):
            app.entry.insert('1.0',text);app.send();wait(root,app);return app.last_answer
        with patch.object(weather,'fetch_weather',side_effect=[weather.WeatherError('テスト通信失敗'),'荒川区の今日の予報\n最高気温：18℃\nhttps://open-meteo.com/']) as fetch:
            assert '市区町村' in ask('今日の天気は？')
            assert '話題を保持' in ask('平塚市')
            assert '最高気温：18℃' in ask('荒川区')
            assert [c.args for c in fetch.call_args_list]==[('平塚市','今日'),('荒川区','今日')]
        assert '回答が未完了' not in app.transcript.get('1.0','end')
        assert '結果：3' in ask('計算: 1+2')
        assert app.service.pending_weather is None
    finally:stop(root,app)
print('Weather UI: missing region -> failed Hiratsuka -> successful Arakawa, no model invocation, topic change: OK')
