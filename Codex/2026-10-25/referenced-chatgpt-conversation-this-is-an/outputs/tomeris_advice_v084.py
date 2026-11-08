"""Focused prompting and bounded practical-advice review for local models."""
import re
from tomeris_compare_v08 import LocalProvider as BaseProvider
from tomeris_provider import ProviderError
from tomeris_guardrails import is_pc_risk_question

from tomeris_context_v084 import SHORT_RULES as DIRECT_RULES


def practical_request(question):
    return (any(word in question for word in ('工夫','コツ','方法','具体策'))
            and not is_pc_risk_question(question)
            and not any(word in question for word in ('AIが','AIは','AIの','トメリスが','トメリスの','できること','支援内容')))


def review_advice(question, answer):
    """Heuristics, not a correctness score. Restrict to practical advice requests."""
    if not practical_request(question):
        return []
    issues=[]
    match=re.search(r'([1-5１-５])\s*(?:つ|個|点|項目)',question)
    if match:
        requested=int(match.group(1))
        count=len(re.findall(r'^\s*(?:\*\*)?\d+[.．、)）]\s*',answer,re.M))
        if count != requested:
            issues.append(f'番号付き項目を正確に{requested}件にする')
    if (re.search(r'(?:アドバイスやサポートを提供|予定の管理や振り返りもサポート|ユーザーと直接的なコミュニケーション|ユーザーの期待や要望を理解|情報のフィルタリングを行い)',answer)
            or re.search(r'(?:AIは|AIが|私は).{0,70}(?:支援|サポート|提供できます)',answer,re.S)):
        issues.append('AIの機能説明ではなくユーザーが行う具体的な行動を答える')
    # Caution on newly introduced labels; this does not establish truth or falsity.
    label = re.search(r'[「『]([^」』]{2,40})[」』]\s*(?:と呼|という(?:方法|手法|時間管理法))', answer)
    if label and label.group(1) not in question:
        issues.append('新しい方法名を付けず平易な手順で説明する（名称の根拠は未確認）')
    if not any(word in question for word in ('詳しく','詳細','長文')) and len(answer) > 600:
        issues.append('各項目1〜2文を目安に短くする')
    return issues


class AdviceProvider(BaseProvider):
    def generate(self,messages):
        self.quality_issues=[]
        self.quality_attempts=1
        users=[m.get('content','') for m in messages if m.get('role')=='user']
        question=users[-1] if users else ''
        # New list: do not modify the frozen comparison context.
        prepared=list(messages)
        answer=super().generate(prepared)
        issues=review_advice(question,answer)
        if issues:
            self.quality_attempts=2
            revised=[{'role':'system','content':'修正事項：'+'。'.join(issues)}]+messages
            try:
                answer=super().generate(revised)
                issues=review_advice(question,answer)
            except ProviderError:
                issues=issues+['再生成に失敗したため初回回答を表示']
        self.quality_issues=issues
        if issues:
            return '【回答品質の注意：'+'／'.join(issues)+'】\n'+answer
        return answer
