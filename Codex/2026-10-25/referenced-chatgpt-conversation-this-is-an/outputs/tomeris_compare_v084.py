"""Local Ollama comparison. Sequential calls, fixed context, no auto-download."""
from copy import deepcopy
import json
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from tomeris_provider import OllamaProvider as BaseProvider, ProviderError
from tomeris_guardrails import (is_direct_pc_action_request, no_pc_action_reply,
    is_pc_risk_question, review_pc_risk_answer, claims_pc_action_completed, pc_risk_fallback)

from tomeris_advice_v084 import AdviceProvider as LocalProvider


def list_models(provider):
    models=provider._request('/api/tags').get('models')
    if not isinstance(models,list):
        raise ProviderError('モデル一覧の形式が不正です。')
    result={}
    for item in models:
        if not isinstance(item,dict):
            continue
        name=item.get('name')
        if (not isinstance(name,str) or not name or name.endswith('-cloud')
                or item.get('remote_host') or item.get('remote_model')):
            continue
        result[name]=item
    return result


def compare(models, question, messages, provider_factory=LocalProvider):
    if len(models)!=2 or models[0]==models[1]:
        raise ProviderError('異なる2つのモデルを指定してください。')
    if not question.strip():
        raise ProviderError('比較する質問を入力してください。')
    if is_direct_pc_action_request(question):
        raise ProviderError(no_pc_action_reply())
    available=list_models(provider_factory())
    if any(name not in available for name in models):
        raise ProviderError('指定モデルが未導入です。/models の名前を正確に指定してください。自動ダウンロードはしません。')
    digests=[available[name].get('digest') for name in models]
    if digests[0] and digests[0]==digests[1]:
        raise ProviderError('同じモデルの別名です。異なるモデルを選んでください。')
    results=[]
    for name in models:
        print(f'比較中: {name} …',flush=True)
        start=perf_counter()
        try:
            answer=provider_factory(model=name).generate(deepcopy(messages))
            status='quality_warning' if answer.startswith('【回答品質の注意：') else 'ok'
            if claims_pc_action_completed(answer):
                answer=no_pc_action_reply()
                status='replaced'
            elif is_pc_risk_question(question) and review_pc_risk_answer(question,answer):
                answer=pc_risk_fallback(question)
                status='replaced'
            results.append({'model':name,'status':status,'answer':answer,'seconds':round(perf_counter()-start,2)})
        except ProviderError as exc:
            results.append({'model':name,'status':'error','answer':str(exc),'seconds':round(perf_counter()-start,2)})
    return results


def display(results):
    for index,item in enumerate(results,1):
        state={'ok':'モデル回答（簡易チェック通過）','replaced':'安全基準で定型回答に置換','error':'取得失敗','quality_warning':'品質上の注意あり'}[item['status']]
        print(f"\n【回答{index} | {item['model']} | {state} | {item['seconds']}秒】\n{item['answer']}")
    print('\n回答時間は参考値です。正確性の点数や自動の勝敗判定ではありません。')


