"""Local Ollama comparison. Sequential calls, fixed context, no auto-download."""
from copy import deepcopy
import json
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from tomeris_provider import OllamaProvider as BaseProvider, ProviderError
from tomeris_guardrails import (is_direct_pc_action_request, no_pc_action_reply,
    is_pc_risk_question, review_pc_risk_answer, claims_pc_action_completed, pc_risk_fallback)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class LocalProvider(BaseProvider):
    def _request(self, path, payload=None, timeout=8):
        if self.base_url not in ('http://localhost:11434','http://127.0.0.1:11434'):
            raise ProviderError('接続先はローカルOllamaに限定されています。')
        body=None if payload is None else json.dumps(payload,ensure_ascii=False).encode('utf-8')
        request=Request('http://127.0.0.1:11434'+path,data=body,headers={'Content-Type':'application/json'})
        try:
            with build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=timeout) as response:
                raw=response.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:
                raise ProviderError('Ollamaの応答が大きすぎます。')
            result=json.loads(raw)
            if not isinstance(result,dict):
                raise ValueError()
            return result
        except HTTPError as exc:
            code=exc.code
            exc.close()
            raise ProviderError(f'Ollama HTTP {code}。モデルと起動状態を確認してください。') from None
        except (URLError,OSError,ValueError):
            raise ProviderError('Ollamaの通信または応答形式を確認してください。') from None

    def generate(self,messages):
        result=self._request('/api/chat',payload={'model':self.model,'messages':messages,'stream':False,
            'keep_alive':0,'options':{'temperature':0.3,'num_ctx':8192,'num_predict':600}},timeout=self.timeout)
        if result.get('done') is not True or result.get('done_reason')=='length':
            raise ProviderError('回答が未完了、または長さ上限に達しました。質問を短くしてください。')
        message=result.get('message')
        answer=message.get('content') if isinstance(message,dict) else None
        if not isinstance(answer,str) or not answer.strip():
            raise ProviderError('Ollamaの回答が空、または形式が不正です。')
        return answer.strip()


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
            status='ok'
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
        state={'ok':'モデル回答（簡易チェック通過）','replaced':'安全基準で定型回答に置換','error':'取得失敗'}[item['status']]
        print(f"\n【回答{index} | {item['model']} | {state} | {item['seconds']}秒】\n{item['answer']}")
    print('\n回答時間は参考値です。正確性の点数や自動の勝敗判定ではありません。')

