"""Short, conditional guidance for local decision and causal analysis.

This changes prompting, not model weights or factual verification.
"""
import re
from tomeris_parallel_collection import DesktopService as BaseService

ANALYSIS = re.compile(r'すべき|した方が|したほうが|断定|原因|おかげ|せいで|状況.*分析|判断.*迷|効果.*あった|効果.*ある')
GUIDANCE = ('\n判断・原因の相談には3点で短く答える。'
            '1. 現時点の判断。ユーザーの報告を検証済みの事実とせず、原因や効果を断定しない。'
            '2. 判断に必要な具体的な情報を最大2つ質問する。'
            '3. 次に確かめる方法を1つ提案する。前後比較なら期間・母数・他の条件の違いを考える。'
            '数値や結果を作らず、今回の質問に即して答える。ジョークは加えない。')


class DesktopService(BaseService):
    def conversation_persona(self, text):
        if ANALYSIS.search(text):
            # Keep the parent's frequency accounting, but do not permit humor
            # for an analytical turn even when casual words also occur.
            return super().conversation_persona('真面目 ' + text) + GUIDANCE
        return super().conversation_persona(text)
