"""Route public-person introductions to source retrieval, with bounded clarification."""
import re
from tomeris_research_freshness import DesktopService as BaseService
from tomeris_auto_research_v029 import instruction

WHO = re.compile(r'(.{1,80}?)(?:って|て|とは|は)(?:誰|だれ)(?:ですか|なの|なのですか)?[？?。！!]*')
ROLE = re.compile(r'(?:YouTuber|ユーチューバー|ゲーム実況者|実況者|配信者|俳優|女優|歌手|作家|漫画家|研究者|スポーツ選手|政治家)(?:の人|の方)?', re.I)


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_person = None

    def clear_tool_context(self):
        self.pending_person = None
        return super().clear_tool_context()

    def prepare_context(self, text):
        selected, _ = instruction(text)
        if selected:
            self.pending_person = None
            return super().prepare_context(text)
        compact = text.strip()
        pending = self.pending_person
        self.pending_person = None
        match = WHO.fullmatch(compact)
        if match:
            name = match[1].strip()
            if name in ('あなた', '君', 'きみ', '私', 'わたし', '僕', 'ぼく', '自分'):
                return super().prepare_context(text)
            self.clear_tool_context()
            if re.fullmatch(r'[A-Za-z0-9_.-]{1,30}', name):
                self.pending_person = name
                return text, self.track(text, '「'+name+'」はどの分野の方ですか？'
                    '「YouTuber」「歌手」のように活動分野を教えてください。'
                    '同名の別人と混同しないよう確認してから、公開プロフィールや活動内容を出典付きで調べます。')
            return text, self.report(name+'について調べて')
        if pending and ROLE.fullmatch(compact.rstrip('。！!')):
            self.clear_tool_context()
            return text, self.report(pending+' '+compact.rstrip('。！!')+'について調べて')
        return super().prepare_context(text)
