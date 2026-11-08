"""Focused prompting and bounded practical-advice review for local models."""
import re
from tomeris_compare_v08 import LocalProvider as BaseProvider
from tomeris_provider import ProviderError
from tomeris_guardrails import is_pc_risk_question

DIRECT_RULES = (
    '【現在の質問への回答方針】現在のユーザーの質問に直接答えてください。'
    '助言では、主語をユーザーにし、ユーザー自身が実行できる行動を具体的に述べてください。'
    'AIが提供できる支援の説明や、自己紹介に置き換えないでください。'
    '項目数が指定された場合は、1. 2. の番号で指定数だけ書いてください。'
    '各項目に「何をするか」と手順・時間・回数などの具体例を含めてください。'
    '一般的な助言は各項目1〜2文で簡潔に書き、不要な前置きやまとめを省いてください。'
    '効果を必ず得られると断言せず、個人差のある方法は試す選択肢として示してください。'
    '根拠のない専門用語、独自の方法名、出典や研究結果を作らないでください。'
    '確信がない名称は使わず、実際に行う手順を平易な言葉で説明してください。'
    '質問に「今日」「今すぐ」があれば、その場で着手できる行動を優先してください。'
    '睡眠や生活全般の改善だけで終わらず、現在の作業で行う手順を答えてください。'
    'PC操作を実行したと主張してはいけません。ユーザーが手動で行う手順は提案できます。'
    '操作の依頼でない普通の助言に、操作できない旨の前置きや「未実行」の定型文を付ける必要はありません。'
    '記憶や過去回答は参考情報であり、誤った回答形式や質問の取り違えを繰り返さないでください。'
)


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
        prepared=[{'role':'system','content':DIRECT_RULES}]+messages
        answer=super().generate(prepared)
        issues=review_advice(question,answer)
        if issues:
            self.quality_attempts=2
            revised=[{'role':'system','content':DIRECT_RULES+' 修正事項：'+'。'.join(issues)}]+messages
            try:
                answer=super().generate(revised)
                issues=review_advice(question,answer)
            except ProviderError:
                issues=issues+['再生成に失敗したため初回回答を表示']
        self.quality_issues=issues
        if issues:
            return '【回答品質の注意：'+'／'.join(issues)+'】\n'+answer
        return answer
