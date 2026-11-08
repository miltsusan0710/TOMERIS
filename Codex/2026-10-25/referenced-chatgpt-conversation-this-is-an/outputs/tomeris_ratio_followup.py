"""Bounded, deterministic follow-ups to the last explicit ratio comparison."""
from fractions import Fraction
from tomeris_ratio_comparison import DesktopService as BaseService, compare_counts, FORM, HELP

FOLLOWUPS = frozenset(('どういうこと', 'つまり', 'つまりどういうこと', 'もう少し説明して',
                      'じゃあ改善してない', '改善してない', '改善した', '改善したの',
                      '改善している', '悪化した', '悪化したの', 'なぜ', 'どうして'))


def explanation(text):
    n1, _, k1, _, n2, _, k2, _ = FORM.fullmatch(text.strip()).groups()
    a, b = Fraction(int(k1), int(n1)), Fraction(int(k2), int(n2))
    change = '増えています' if b > a else '減っています' if b < a else '同じです'
    meaning = ('不良・ミスなど少ない方がよい対象なら、割合の増加は改善ではありません。'
               if b > a else '不良・ミスなど少ない方がよい対象なら、割合は望ましい方向に変化しています。'
               if b < a else '割合で見る限り変化はありません。')
    return ('母数に対する対象数の割合は' + change + '。件数だけで比べると、母数の違いを見落とします。\n'
            + meaning + ('成功など多い方がよい対象では評価が逆になります。' if a != b else '')
            + '何を数えたかは、この数値だけでは特定できません。'
            '原因や施策の効果は、この比較だけでは断定できません。\n\n')


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ratio_snapshot = None

    def clear_tool_context(self):
        self.ratio_snapshot = None
        return super().clear_tool_context()

    def prepare_context(self, text):
        compact = text.strip().rstrip('？?。！!')
        if compact in FOLLOWUPS:
            snapshot = self.ratio_snapshot
            if snapshot is not None:
                return text, self.save_answer(text, snapshot)
            # Other active tools retain their own interpretation of a follow-up.
            return super().prepare_context(text)
        self.ratio_snapshot = None
        result = compare_counts(text)
        query, answer = super().prepare_context(text)
        if result is not None and result != HELP and answer is not None:
            self.ratio_snapshot = explanation(text) + result
        return query, answer
