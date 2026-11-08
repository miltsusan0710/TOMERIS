"""Read-only prompt diagnosis; no memory writes, downloads or cloud calls."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from time import perf_counter
import tomeris_v082 as app
from tomeris_advice_v082 import DIRECT_RULES
from tomeris_compare_v08 import LocalProvider, list_models
from tomeris_memory_engine import MemoryStore
from tomeris_provider import ProviderError
from tomeris_guardrails import is_direct_pc_action_request, claims_pc_action_completed

ROOT=Path(__file__).resolve().parent
QUESTION='今日の作業に集中するための工夫を3つ挙げて'
SHORT='日本語で質問に直接答えてください。ユーザーが今すぐ実行できる行動を、番号付き3項目、各1文で述べてください。前置き・まとめ・方法名は不要です。PC操作を実行したと主張しないでください。'

class ReadOnlyStore(MemoryStore):
    def __init__(self,path,knowledge_dir):
        self.path=Path(path)
        self.knowledge_dir=Path(knowledge_dir)
        self.last_backup=None
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(data,dict):
            raise ValueError('記憶の形式が不正です')
        for key in ('memories','growth_log','conversations'):
            if not isinstance(data.get(key),list):
                raise ValueError('記憶の配列が不正です: '+key)
        self.data=data
    def save(self):
        raise RuntimeError('診断では記憶を保存できません')
    def _save_data(self,*args,**kwargs):
        raise RuntimeError('診断では記憶を保存できません')

class EmptyContext:
    def build_context(self,text):
        return '関連する記憶はありません。'
    def recent_conversations(self,limit=3):
        return []

class DiagnosticProvider(LocalProvider):
    def _request(self,path,payload=None,timeout=8):
        if payload is not None:
            payload=deepcopy(payload)
            payload.setdefault('options',{})['seed']=42
        return super()._request(path,payload=payload,timeout=timeout)

def profiles(question,store):
    def current(context):
        # Reproduce the first v0.8.2 generation, including its prepended rule.
        return [{'role':'system','content':DIRECT_RULES}]+app.build_messages(context,question)
    return [
        ('A: 短い指示・記憶なし',[{'role':'system','content':SHORT},{'role':'user','content':question}]),
        ('B: 現在の長い指示・記憶なし',current(EmptyContext())),
        ('C: 現在の長い指示・記憶あり',current(store)),
    ]

def main(argv=None):
    parser=argparse.ArgumentParser(description='トメリスの読み取り専用回答診断')
    parser.add_argument('--model',default='qwen2.5:3b')
    parser.add_argument('--memory',type=Path,default=ROOT/'tomeris_memory_v082.json')
    args=parser.parse_args(argv)
    try:
        provider=DiagnosticProvider(model=args.model)
        available=list_models(provider)
        if args.model not in available:
            raise ProviderError('指定モデルがローカル一覧にありません。ダウンロードはしません。')
        store=ReadOnlyStore(args.memory,ROOT/'knowledge')
        cases=profiles(QUESTION,store)
    except (OSError,ValueError,ProviderError) as exc:
        print('診断を開始できません: '+str(exc))
        return 2
    print('同じモデル・同じ質問で3条件を順に生成します。再生成・保存はしません。')
    print('BとCの指示は同じで、Cだけローカル記憶・直近会話・関連知識が加わります。')
    print('モデル: '+args.model+' / 質問: '+QUESTION)
    successes=0
    for title,messages in cases:
        print('\n'+title+f'（入力 {sum(len(m["content"]) for m in messages)}文字）生成中…',flush=True)
        start=perf_counter()
        try:
            answer=provider.generate(messages)
            if claims_pc_action_completed(answer):
                print('注意: 以下の回答には未実装のPC操作の実行宣言が含まれる可能性があります。操作は実行していません。')
            print(answer)
            print(f'回答 {len(answer)}文字 / {perf_counter()-start:.2f}秒',flush=True)
            successes+=1
        except ProviderError as exc:
            print('取得失敗: '+str(exc))
    print('\n診断終了。記憶・比較履歴は変更していません。')
    print('1回の結果では原因を断定できません。速度はモデル読込・生成文字数にも左右されます。')
    return 0 if successes==3 else 1

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\n診断を中止しました。記憶は変更していません。')
        raise SystemExit(130)
