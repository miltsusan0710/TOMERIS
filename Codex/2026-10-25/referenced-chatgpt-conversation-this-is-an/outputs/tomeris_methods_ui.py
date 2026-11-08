import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import webbrowser
from tomeris_search_methods import browser_search_url,MethodError

class MethodsPanel:
    def __init__(self,app):
        self.app=app
        self.window=tk.Toplevel(app.root);self.window.title('調査方法とGoogle検索');self.window.geometry('780x800');self.window.minsize(640,720)
        self.window.transient(app.root);self.window.grab_set();self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1);self.window.rowconfigure(1,weight=1)
        self.tabs=ttk.Notebook(self.window);self.tabs.grid(row=1,column=0,sticky='nsew',padx=12,pady=8)
        self.search_tab=ttk.Frame(self.tabs);self.settings_tab=ttk.Frame(self.tabs)
        self.tabs.add(self.search_tab,text='検索・確認');self.tabs.add(self.settings_tab,text='設定・APIキー')
        for tab in (self.search_tab,self.settings_tab):tab.columnconfigure(0,weight=1)
        self.search_tab.rowconfigure(4,weight=1)
        ttk.Label(self.window,text='調査方法を選ぶ',font=('Yu Gothic UI',16,'bold')).grid(row=0,column=0,sticky='w',padx=16,pady=12)
        ttk.Label(self.settings_tab,text='調査に使う方法を選択します。\nAPIは利用枠を消費し、料金が発生する場合があります。',wraplength=580,font=('Yu Gothic UI',9)).grid(row=0,column=0,sticky='ew',padx=16,pady=5)
        self.mode=tk.StringVar(value=app.service.methods.mode)
        self.mode_box=ttk.Combobox(self.settings_tab,textvariable=self.mode,values=(['自動'] if app.service.methods.__class__.__name__=='AutoMethods' else [])+['Wikipedia（日本語）','Wikipedia（日英）','Brave API','併用（Wikipedia＋Brave）','Bing RSS（試験）'],state='readonly')
        self.mode_box.grid(row=1,column=0,sticky='ew',padx=16,pady=6)
        fields=ttk.Frame(self.settings_tab);fields.grid(row=2,column=0,sticky='ew',padx=16);fields.columnconfigure(1,weight=1)
        self.brave=ttk.Entry(fields,show='●',width=1);self.gemini=ttk.Entry(fields,show='●',width=1);self.model=ttk.Entry(fields,width=1)
        self.model.insert(0,app.service.methods.gemini_model)
        for i,(label,widget) in enumerate([('Brave APIキー',self.brave),('Gemini APIキー',self.gemini),('GeminiモデルID',self.model)]):
            ttk.Label(fields,text=label,font=('Yu Gothic UI',9)).grid(row=i,column=0,sticky='w',padx=(0,8),pady=4);widget.grid(row=i,column=1,sticky='ew',pady=4)
        ttk.Label(self.settings_tab,text='キーはこの起動中のみ保持。空欄なら現在のキーを維持します。',wraplength=580,font=('Yu Gothic UI',9)).grid(row=3,column=0,sticky='ew',padx=16,pady=5)
        bar=ttk.Frame(self.settings_tab);bar.grid(row=4,column=0,sticky='ew',padx=16,pady=5)
        self.save_button=ttk.Button(bar,text='この設定を使う',command=self.save);self.save_button.pack(side='left')
        self.clear_button=ttk.Button(bar,text='APIキーを消去',command=self.clear);self.clear_button.pack(side='right')
        queryframe=ttk.Frame(self.search_tab);queryframe.grid(row=0,column=0,sticky='ew',padx=16,pady=8);queryframe.columnconfigure(0,weight=1)
        ttk.Label(queryframe,text='検索する文章（この文章だけを外部へ送ります）',font=('Yu Gothic UI',9)).grid(row=0,column=0,sticky='w')
        self.query=ttk.Entry(queryframe,width=1);self.query.grid(row=1,column=0,sticky='ew',pady=4)
        self.query.insert(0,app.entry.get('1.0','end-1c').strip())
        buttons=ttk.Frame(self.search_tab);buttons.grid(row=1,column=0,sticky='ew',padx=16,pady=4)
        self.browser_buttons=[]
        for name in ('Google','Bing','DuckDuckGo'):
            b=ttk.Button(buttons,text=name+'で開く',command=lambda n=name:self.open_browser(n));b.pack(side='left',padx=(0,6));self.browser_buttons.append(b)
        actions=ttk.Frame(self.search_tab);actions.grid(row=2,column=0,sticky='ew',padx=16,pady=5)
        self.probe_button=ttk.Button(actions,text='選択した方法を試す',command=self.probe);self.probe_button.pack(side='left')
        self.google_button=ttk.Button(actions,text='Google APIで調べて表示',command=self.google);self.google_button.pack(side='left',padx=6)
        self.message=tk.StringVar(value=self.status_text())
        ttk.Label(self.search_tab,textvariable=self.message,wraplength=580,font=('Yu Gothic UI',9)).grid(row=3,column=0,sticky='ew',padx=16,pady=5)
        self.detail=ScrolledText(self.search_tab,width=1,height=2,wrap='word',state='disabled');self.detail.grid(row=4,column=0,sticky='nsew',padx=16,pady=6)
        self.exit_button=ttk.Button(self.window,text='閉じる',command=self.close);self.exit_button.grid(row=2,column=0,sticky='e',padx=16,pady=(0,10))
        self.controls=[self.brave,self.gemini,self.model,self.query,self.save_button,self.clear_button,self.probe_button,self.google_button,self.exit_button]+self.browser_buttons
        self.state()
    def status_text(self):
        m=self.app.service.methods
        return f'使用中：{m.mode}\nBraveキー：'+('設定済み（実行時に確認）' if m.brave_key else '未設定')+' ／ Geminiキー：'+('設定済み（実行時に確認）' if m.gemini_key else '未設定')
    def state(self):
        if not self.window.winfo_exists():return
        active=not self.app.busy and not self.app.closing
        for w in self.controls:w.configure(state='normal' if active else 'disabled')
        self.mode_box.configure(state='readonly' if active else 'disabled')
    def run(self,operation,callback,label):
        if self.app.busy or self.app.closing:return
        def work():
            try:result=(None,operation())
            except (MethodError,ValueError,OSError) as exc:result=(str(exc),None)
            except Exception:result=('処理を完了できませんでした。設定と接続を確認してください。',None)
            return loaded,result
        def loaded(result):
            if not self.window.winfo_exists():return
            error,value=result
            self.state()
            if error:self.message.set(error)
            else:callback(value)
            self.state()
        self.app.submit('plan_result',work,label);self.state()
    def save(self):
        m=self.app.service.methods;mode=self.mode.get();brave=self.brave.get().strip() or m.brave_key;gemini=self.gemini.get().strip() or m.gemini_key;model=self.model.get().strip()
        def saved(value):
            self.brave.delete(0,'end');self.gemini.delete(0,'end');self.message.set(value+'\n'+self.status_text());self.tabs.select(self.search_tab)
        self.run(lambda:self.app.service.configure_methods(mode,brave,gemini,model),saved,'調査方法を変更しています…')
    def clear(self):
        mode=self.app.service.methods.mode;model=self.app.service.methods.gemini_model
        def cleared(value):
            self.brave.delete(0,'end');self.gemini.delete(0,'end');self.message.set('両方のAPIキーを消去しました。')
        self.run(lambda:self.app.service.configure_methods(mode,'','',model),cleared,'APIキーを消去しています…')
    def text(self,value):
        self.detail.configure(state='normal');self.detail.delete('1.0','end');self.detail.insert('end',value);self.detail.configure(state='disabled')
    def open_browser(self,name):
        if self.app.busy:return
        try:
            url=browser_search_url(name,self.query.get())
            if not webbrowser.open(url):raise MethodError('ブラウザーを開けませんでした。')
            self.message.set(name+'の検索画面を開きました。結果を自動取得したわけではありません。URLを会話欄に貼って追加調査できます。')
        except (MethodError,OSError,webbrowser.Error) as exc:self.message.set(str(exc))
    def probe(self):
        query=self.query.get().strip()
        def loaded(value):
            rows,notes=value;self.text('\n'.join(notes)+'\n\n'+'\n\n'.join(r['title']+'\n'+r['url'] for r in rows));self.message.set('取得結果です。関連性・正確さの保証ではありません。未保存の設定は使いません。')
        self.run(lambda:self.app.service.methods.candidates(query),loaded,'選択した調査方法を確認しています…')
    def google(self):
        query=self.query.get().strip()
        def loaded(path):
            try:opened=webbrowser.open(path.resolve().as_uri())
            except (OSError,webbrowser.Error):opened=False
            if opened:self.message.set('Google APIの出典付き回答をブラウザーで開きました。内容は未検証です。')
            else:self.message.set('レポートを保存しましたがブラウザーを開けませんでした。');self.text(str(path))
        self.run(lambda:self.app.service.google_grounded_report(query),loaded,'Google APIで検索しています（利用枠を消費します）…')
    def close(self):
        if self.app.busy:return
        self.window.destroy()
