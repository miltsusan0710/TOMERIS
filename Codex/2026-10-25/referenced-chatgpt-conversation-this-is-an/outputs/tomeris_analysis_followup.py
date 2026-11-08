"""One immediate data reply inherits analysis guidance, never factual authority."""
import re
from tomeris_analysis_style import DesktopService as BaseService, ANALYSIS, GUIDANCE
from tomeris_persona import DesktopService as PersonaService

DATA_START = re.compile(r'^(?:前|後|変更|導入|短縮|期間|人数|参加者|作業|件数|ミス|遅刻|売上|広告費|比較|どちらも|両方|それぞれ|同じ|[0-9０-９])')
NUMBER = re.compile(r'[0-9０-９]')
NEW_TOPIC = re.compile(r'天気|地震|予定|調べ|検索|別の話|話題|計算[:：]')
FOLLOWUP = ('\n直前の分析相談への追加データとして扱う。会話中の数値・単位・前後の対応を変えない。'
            '件数だけで改善と断定せず母数や期間の違いを確認する。'
            '不明な母数・条件は補わず、未確認と伝える。')


class DesktopService(BaseService):
    def conversation_persona(self, text):
        turns = self.session_turns
        previous = turns[-1][0] if turns else ''
        # Only the immediately preceding analytical question is eligible.
        # Raw user text remains user-role history, not system instructions.
        follows = (not ANALYSIS.search(text) and ANALYSIS.search(previous)
                   and len(text) <= 400 and DATA_START.search(text.strip())
                   and NUMBER.search(text) and not NEW_TOPIC.search(text))
        if follows:
            return PersonaService.conversation_persona(self, '真面目 ' + text) + GUIDANCE + FOLLOWUP
        return super().conversation_persona(text)
