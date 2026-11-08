"""User initiated multimedia and bounded multi-request UI."""
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tomeris_multimodal import image_answer
from tomeris_speech_control import speech, SpeechCancelled, finish_audio
import threading
from tomeris_calculator import expression_from, calculate

def plan_requests(text):
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    if not 1<=len(lines)<=4 or any(len(line)>500 for line in lines):raise ValueError('1行1依頼で最大4件、各500文字までです。')
    plan=[]
    for line in lines:
        expr=expression_from(line)
        if expr:plan.append(('計算',expr))
        elif line.startswith(('調査:','調査：')) and line[3:].strip():plan.append(('調査',line[3:].strip()))
        else:raise ValueError('計算式、または「調査: 対象名」の形で入力してください。')
    return plan

def run_requests(plan,service,model):
    if not 1<=len(plan)<=4:raise ValueError('依頼数の上限は4件です。')
    results=[]
    for kind,query in plan:
        try:
            if kind=='計算':answer=calculate(query)
            elif kind=='調査':answer=service.research(query,model)
            else:raise ValueError('この操作は対応していません。')
        except Exception as exc:answer='処理できませんでした：'+str(exc)
        results.append(f'【{len(results)+1} / {kind}：{query}】\n{answer}')
    return '\n\n'.join(results)

def attach_menu(app,menu):
    app.audio_active=False
    app.audio_cancel=threading.Event()
    def ready():return app.service is not None and not app.busy and not app.closing
    def job(fn,done,label):
        if not ready():return
        def work():return done,fn()
        app.submit('plan_result',work,label)
    def audio_job(action,text,done,label):
        if not ready():return
        cancel=threading.Event();app.audio_cancel=cancel;app.audio_active=True
        def completed(outcome):finish_audio(app,cancel,done,outcome)
        def work():
            try:outcome=('ok',speech(action,text,cancel))
            except SpeechCancelled:outcome=('cancelled',None)
            except Exception as exc:outcome=('error',str(exc))
            return completed,outcome
        if not app.submit('plan_result',work,label):app.audio_active=False
    def stop():
        if app.audio_active:
            app.audio_cancel.set()
            app.status.set('音声処理を停止しています…')
    def answer(text):app.append('トメリス',text)
    def image():
        if not ready():return
        path=filedialog.askopenfilename(parent=app.root,title='読み取る画像を選択（ローカル処理）',filetypes=[('画像','*.png *.jpg *.jpeg')])
        if not path:return
        question=simpledialog.askstring('画像への質問','画像について知りたいことを入力してください。画像・回答は自動保存しません。',initialvalue='この画像の内容を説明してください。',parent=app.root)
        if not question:return
        model='gemma3:4b' if 'gemma3:4b' in app.models else app.model.get()
        job(lambda:image_answer(path,question,model),answer,'選択した画像をローカルAIで読み取っています…')
    def listen():
        if not ready():return
        def done(data):
            app.entry.insert('end',('\n' if app.entry.get('1.0','end-1c') else '')+data['text'])
            answer('聞き取った文字を入力欄に入れました。内容を確認して送信してください。')
        audio_job('listen','',done,'マイクで聞き取っています（最大20秒・終了後に文字を確認）…')
    def speak():
        if not ready() or not app.last_answer:return
        text=app.last_answer
        if len(text)>1000:
            messagebox.showinfo('読み上げ','読み上げは1000文字以内の回答に対応しています。',parent=app.root);return
        audio_job('speak',text,lambda data:None,'回答を読み上げています…')
    def status():
        audio_job('status','',lambda d:messagebox.showinfo('音声機能','日本語音声認識：'+('利用可能' if d['recognition'] else '未導入')+'\n日本語読み上げ：'+('利用可能' if d['speech'] else '未導入'),parent=app.root),'音声機能を確認しています…')
    def batch():
        if not ready():return
        window=tk.Toplevel(app.root);window.title('まとめて依頼（最大4件）');window.geometry('640x360')
        tk.Label(window,text='計算式、または「調査: 対象名」を1行ずつ入力。\n調査先は既存の方法選択に従います。各依頼を順番に処理します。').pack(pady=8)
        entry=tk.Text(window,height=9);entry.pack(fill='both',expand=True,padx=12)
        def execute():
            if not ready():return
            try:plan=plan_requests(entry.get('1.0','end'))
            except ValueError as exc:messagebox.showerror('入力の確認',str(exc),parent=window);return
            model=app.model.get();window.destroy()
            job(lambda:run_requests(plan,app.service,model),answer,'複数の依頼を調査・計算に振り分けています…')
        tk.Button(window,text='実行',command=execute).pack(pady=10)
    media=tk.Menu(menu,tearoff=False)
    for title,fn in [('画像を選んで質問',image),('音声を入力（マイク開始）',listen),('最後の回答を読み上げ',speak),('音声機能を確認',status),('音声を停止',stop),('まとめて依頼（調査・計算）',batch)]:media.add_command(label=title,command=fn)
    menu.add_cascade(label='画像・音声・依頼',menu=media)

    return dict(image=image,listen=listen,speak=speak,status=status,batch=batch,stop=stop)
