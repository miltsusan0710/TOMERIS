"""Read-only presentation of acquisition outcomes, not correctness scores."""
LABELS = {'evidence': '本文・引用あり', 'no_candidate': '候補なし',
          'no_evidence': '引用根拠なし', 'retrieval_error': '本文取得エラー',
          'legacy': '旧形式（理由未記録）'}

def summarize(history):
    counts = dict.fromkeys(LABELS, 0)
    for row in history:
        counts[row.get('outcome', 'legacy')] += 1
    return counts

def format_summary(counts):
    return '\n'.join(f'{label}：{counts.get(key, 0)}件' for key, label in LABELS.items()) + (
        '\n1件は取得方法1回の記録です。同じテーマでも複数件になります。'
        '\n本文取得エラーは優先順の計算から除外します。旧形式は再分類せず従来どおり計算します。'
        '\n成功・不成功の取得経験で順序を調整します。正しさの採点や会話モデルの訓練ではありません。')
