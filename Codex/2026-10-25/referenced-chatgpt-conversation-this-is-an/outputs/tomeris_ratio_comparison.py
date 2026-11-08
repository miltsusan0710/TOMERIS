"""Deterministic comparison for an explicitly bounded before/after grammar."""
import re
from fractions import Fraction
from decimal import Decimal, localcontext
from tomeris_analysis_style import DesktopService as BaseService

FORM = re.compile(
    r'(?:変更)?前は\s*([0-9]{1,10})(個|件|人|回)中\s*([0-9]{1,10})(個|件|人|回)'
    r'\s*[、,]\s*(?:変更)?後は\s*([0-9]{1,10})(個|件|人|回)中\s*([0-9]{1,10})(個|件|人|回)'
    r'(?:[。.]\s*期間は(?:どちらも|両方)?[0-9]{1,4}(?:日|週間|か月|ヶ月|時間))?[。.]?'
)
HELP = ('前後の母数・対象数を一意に確認できません。単位をそろえて'
        '「前は100個中10個、後は40個中8個」の形で入力してください。'
        '母数は1以上、対象数は0以上で母数以下にしてください。')


def percent(value):
    with localcontext() as context:
        context.prec = 32
        number = Decimal(value.numerator) / Decimal(value.denominator)
        return format(number, '.2f')


def compare_counts(text):
    text = text.strip()
    if not (re.match(r'^(?:変更)?前は', text) and '中' in text and '後は' in text):
        return None
    match = FORM.fullmatch(text)
    if not match:
        return HELP
    n1, u1, k1, u2, n2, u3, k2, u4 = match.groups()
    n1, k1, n2, k2 = map(int, (n1, k1, n2, k2))
    if len({u1, u2, u3, u4}) != 1 or not (0 < n1 <= 10**9 and 0 < n2 <= 10**9
                                            and 0 <= k1 <= n1 and 0 <= k2 <= n2):
        return HELP
    before, after = Fraction(k1 * 100, n1), Fraction(k2 * 100, n2)
    diff = after - before
    direction = '増加' if diff > 0 else '減少' if diff < 0 else '変化なし'
    count_diff = k2 - k1
    count_direction = '増加' if count_diff > 0 else '減少' if count_diff < 0 else '変化なし'
    return (f'入力された数値の比較です（外部確認なし）。\n'
            f'前：{n1}{u1}中{k1}{u1} → {percent(before)}％\n'
            f'後：{n2}{u1}中{k2}{u1} → {percent(after)}％\n'
            f'対象数：{abs(count_diff)}{u1}の{count_direction}\n'
            f'割合：{percent(abs(diff))}ポイントの{direction}\n'
            '割合の表示は小数第2位まで丸めています。件数と割合の変化は別です。\n'
            '不良やミスの割合なら、増加を改善とは扱えません。'
            'この計算だけでは原因・施策の効果・統計的な有意差は判断できません。'
            '対象の定義、比較期間、その他の条件が同じか確認してください。')


class DesktopService(BaseService):
    def prepare_context(self, text):
        result = compare_counts(text)
        if result is not None:
            self.clear_tool_context()
            return text, self.save_answer(text, result)
        return super().prepare_context(text)
