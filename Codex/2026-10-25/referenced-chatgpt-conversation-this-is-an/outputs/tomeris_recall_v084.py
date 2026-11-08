"""Source-preserving goal recall. No model rewriting or memory mutation."""
import re


def goal_recall(store,text):
    query=re.sub(r'^記憶を参照して[：:]\s*','',text.strip()).rstrip('。？！?!')
    if not re.fullmatch(r'(?:私の|トメリスの|保存した|記憶した)?(?:最重要)?目標(?:を教えて(?:ください)?|は何(?:ですか)?|は)',query):
        return None
    # Explicit goal recall uses original records, not past model-generated conversations.
    records=store.data.get('memories',[])
    selected=[r for r in records if isinstance(r,dict) and
              (r.get('category')=='目標' or '目標' in str(r.get('text','')))]
    if query.startswith('トメリスの'):
        selected=[r for r in selected if 'トメリス' in str(r.get('text',''))]
    if not selected:
        return '長期記憶に該当する目標の記録が見つかりません。推測では補いません。/remember で登録できます。'
    lines=['目標について保存されている原文です。AIによる要約ではありません。']
    for record in selected[-3:]:
        original=str(record.get('text',''))
        clipped=original[:1000]
        lines.append(f"\n[{record.get('id','ID不明')}]\n「{clipped}」"+('（以降省略）' if len(original)>1000 else ''))
        if re.search(r'トメリス(?:の最重要目標|の目標|の開発目標|を開発)',original):
            lines.append('この記録はトメリスの役割・開発目標について述べています。ユーザー自身がAIになるという意味ではありません。')
        else:
            lines.append('目標の主体は原文で確認してください。分類名だけでは個人の目標と断定しません。')
    lines.append('\n目標や判断原則の記録は、成果や勝利の保証を意味しません。')
    return '\n'.join(lines)
