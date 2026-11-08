"""Desktop service; one owner per data directory, serialized by the UI worker."""
from copy import deepcopy
from pathlib import Path
import json
import os
import re
import tomeris_v084 as core
from tomeris_memory_engine import MemoryStore
from tomeris_provider import ProviderError
from tomeris_compare_v084 import LocalProvider, list_models
from tomeris_pc_info_v06 import pc_info
from tomeris_desktop_compare import compare

ROOT=Path(__file__).resolve().parent

class SessionLock:
    def __init__(self,path):
        self.handle=open(path,'a+b')
        self.handle.seek(0,2)
        if self.handle.tell()==0:
            self.handle.write(b'0'); self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError('トメリスは既に起動しています。開いているウィンドウをご確認ください。') from None
    def close(self):
        self.handle.close()

class DesktopService:
    def __init__(self,data_dir=None,source=None,demo=False):
        self.data_dir=Path(data_dir or ROOT/'tomeris_desktop_data')
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self.lock=SessionLock(self.data_dir/'session.lock')
        self.demo=demo
        self.model_names=[]
        self.imported=False
        self.memory_path=self.data_dir/'tomeris_memory.json'
        try:
            source=Path(source) if source else ROOT/'tomeris_memory_v084.json'
            if not demo and not self.memory_path.exists() and source.exists():
                core.import_memory(source,self.memory_path)
                self.imported=True
            self.store=MemoryStore(self.memory_path,ROOT/'knowledge')
        except Exception:
            self.close()
            raise
    def close(self):
        self.lock.close()
    def mutate(self,func):
        before=deepcopy(self.store.data)
        try:
            return func()
        except Exception:
            self.store.data=before
            raise
    def models(self):
        if self.demo:
            self.model_names=['qwen2.5:3b','qwen2.5:1.5b']
        else:
            self.model_names=list(list_models(LocalProvider()))
        return self.model_names
    def chat(self,text,model,use_memory=False):
        text=text.strip()
        if not text:
            raise ValueError('質問を入力してください。')
        if text.startswith('/'):
            raise ValueError('この画面では左のボタンをお使いください。質問は通常の文章で入力できます。')
        query=('記憶を参照して：' if use_memory else '')+text
        if self.demo:
            answer='これは画面確認用の応答です。実際のモデルには接続していません。'
        elif core.is_mission_question(query):
            answer=core.mission_answer()
        else:
            # Goal recall and operation refusal remain available when Ollama is offline.
            recalled=core.goal_recall(self.store,query)
            if recalled is not None:
                answer=recalled
            elif core.is_direct_pc_action_request(query):
                answer=core.no_pc_action_reply()
            else:
                if model not in self.model_names:
                    raise ProviderError('モデルが未確認です。「接続を確認」を押し、Ollamaの起動をご確認ください。')
                answer=core.generate_checked_response(LocalProvider(model=model),self.store,query)
        try:
            self.mutate(lambda:self.store.add_conversation(query,answer))
            return answer
        except OSError:
            return answer+'\n\n【保存できませんでした】空き容量と保存先の権限を確認してください。'
    def compare(self,text,models,progress):
        if not text.strip():
            raise ValueError('比較したい質問を入力してください。')
        if self.demo:
            results=[{'model':name,'status':'ok','answer':'画面確認用の回答です。','seconds':0} for name in models]
        else:
            results=compare(models,text,core.build_messages(self.store,text),progress=progress)
        if any(r['status']!='error' for r in results):
            def save():
                records=self.store.data.setdefault('comparisons',[])
                if not isinstance(records,list):
                    raise ValueError('比較記録の形式を確認してください。')
                records.append({'question':text,'results':results})
                self.store.save()
            try:
                self.mutate(save)
            except (OSError,ValueError):
                return format_comparison(results)+'\n【表示した比較を保存できませんでした】'
        return format_comparison(results)
    def remember(self,text,category):
        text=text.strip()
        if not text:
            raise ValueError('記憶する内容を入力してください。')
        normalized=re.sub(r'\s+','',text).casefold()
        for record in self.store.data['memories']:
            if isinstance(record,dict) and re.sub(r'\s+','',str(record.get('text',''))).casefold()==normalized:
                return '同じ内容が既に保存されています。'
        result=self.mutate(lambda:self.store.add_memory(category,text))
        return f"長期記憶 {result['id']} として保存しました。"
    def view(self,kind):
        if kind=='pc':
            return 'PC情報（この画面のみ。AI送信・履歴保存なし）\n'+json.dumps(pc_info(),ensure_ascii=False,indent=2)
        if kind=='persona':
            return core.read_core()
        if kind=='memories':
            rows=self.store.data['memories']
            return '\n\n'.join(f"[{r.get('id','')}] {r.get('category','')}\n{r.get('text','')}" for r in rows if isinstance(r,dict)) or '長期記憶はまだありません。'
        if kind=='history':
            rows=self.store.recent_conversations(20)
            return '\n\n'.join(f"{r.get('timestamp','')}\nあなた：{r.get('user','')}\nトメリス：{r.get('tomeris','')}" for r in rows) or '会話履歴はまだありません。'
        if kind=='comparisons':
            rows=self.store.data.get('comparisons',[])
            if not isinstance(rows,list):
                return '比較記録の形式を確認してください。'
            return '\n\n'.join('質問：'+str(r.get('question',''))+'\n'+format_comparison(r.get('results',[])) for r in rows[-5:] if isinstance(r,dict)) or '比較記録はまだありません。'
        raise ValueError('表示内容が不明です。')

def format_comparison(results):
    labels={'ok':'回答','error':'取得失敗','replaced':'定型回答へ切替','quality_warning':'品質上の注意あり'}
    if not isinstance(results,list):
        return '比較結果の形式が不正です。'
    return '\n\n'.join(f"【{r.get('model','不明')}／{labels.get(r.get('status'),'状態不明')}／{r.get('seconds','?')}秒】\n{r.get('answer','')}" for r in results if isinstance(r,dict))
