"""Cancelable local speech child; never stops unrelated processes."""
import base64,json,os,subprocess,time
from pathlib import Path
from tomeris_multimodal import SPEECH_SCRIPT

class SpeechCancelled(Exception):pass

def speech(action,text='',cancel=None):
    if action not in ('listen','speak','status'):raise ValueError('不明な音声操作です。')
    if action=='speak' and (not text.strip() or len(text)>1000):raise ValueError('読み上げは1〜1000文字です。')
    if cancel is not None and cancel.is_set():raise SpeechCancelled()
    exe=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    args=[str(exe),'-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(SPEECH_SCRIPT.encode('utf-16-le')).decode('ascii')]
    process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    deadline=time.monotonic()+({'listen':20,'speak':120,'status':15}[action])
    data=json.dumps({'action':action,'text':text},ensure_ascii=False)
    try:
        while True:
            if cancel is not None and cancel.is_set():raise SpeechCancelled()
            if time.monotonic()>=deadline:raise ValueError('音声処理を時間制限で停止しました。')
            try:
                stdout,_=process.communicate(input=data,timeout=.1)
                break
            except subprocess.TimeoutExpired:data=None
        if cancel is not None and cancel.is_set():raise SpeechCancelled()
        try:result=json.loads(stdout.lstrip('\ufeff').strip())
        except ValueError as exc:raise ValueError('Windowsの音声機能を利用できませんでした。') from exc
        if not isinstance(result,dict) or process.returncode or result.get('error'):raise ValueError(result.get('error','音声処理に失敗しました。') if isinstance(result,dict) else '音声処理に失敗しました。')
        return result
    finally:
        if process.poll() is None:process.kill()
        process.communicate()

def finish_audio(app,cancel,done,outcome):
    """Main-thread delivery also checks cancellation after a queued completion."""
    app.audio_active=False
    if app.closing:return
    if cancel.is_set() or outcome[0]=='cancelled':
        app.append('お知らせ','音声処理を停止しました。聞き取った内容は追加していません。')
    elif outcome[0]=='error':app.append('お知らせ',outcome[1])
    else:done(outcome[1])
