"""Exact-name encyclopedia introductions; no model-written biographies."""
import re
import unicodedata
from datetime import datetime, timezone, timedelta
from tomeris_people import DesktopService as BaseService, WHO, ROLE
from tomeris_search_methods import wikipedia_search, wikipedia_page, MethodError
from tomeris_auto_research_v029 import instruction


def compact(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).casefold()


def same_name(title, name):
    return compact(re.sub(r'\s*[（(].*?[）)]$', '', title)) == compact(name)


def introduction(page, name, role):
    if not same_name(page['title'], name):
        return ''
    lead = re.split(r'\n\s*==', page['text'], maxsplit=1)[0].strip()
    first = re.split(r'(?<=[。])', lead, maxsplit=1)[0].strip()
    if not 20 <= len(first) <= 350 or not compact(first).startswith(compact(name)) or 'は、' not in first:
        return ''
    if role:
        group = ('youtuber', 'ユーチューバー') if compact(role) in ('youtuber', 'ユーチューバー') else (compact(role),)
        if not any(word in compact(first) for word in group):
            return ''
    return first


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_request = None

    def prepare_context(self, text):
        target = None
        match = WHO.fullmatch(text.strip())
        pending = self.pending_person
        if match and match[1].strip() not in ('あなた','君','きみ','私','わたし','僕','ぼく','自分'):
            target = (match[1].strip(), None)
        elif pending and ROLE.fullmatch(text.strip().rstrip('。！!')):
            target = (pending, text.strip().rstrip('。！!'))
        self.profile_request = target if not instruction(text)[0] else None
        try:
            return super().prepare_context(text)
        finally:
            self.profile_request = None

    def report(self, question, progress=None, model=None):
        if not self.profile_request or self.methods.mode != '自動':
            return super().report(question, progress, model)
        name, role = self.profile_request
        self.research_source_snapshot = None
        self.last_evidence_items = []
        self.last_evidence_urls = set()
        self.last_research_request = None
        self.followup_seen_urls = set()
        if self.demo:
            return self.track(question, '画面確認用：人物紹介の実検索は行っていません。')
        try:
            candidates = [row for row in wikipedia_search(name) if same_name(row['title'], name)]
            matches = []
            for row in candidates[:3]:
                page = wikipedia_page(row)
                quote = introduction(page, name, role)
                if quote:
                    matches.append((page, quote))
            if len(matches) != 1:
                return self.track(question, '「'+name+'」の人物紹介を一意に確認できませんでした。'
                    '本人の公式プロフィールURL、または正式な活動名を教えてください。別人の情報では補いません。')
        except MethodError:
            return self.track(question, '「'+name+'」の紹介資料を取得できませんでした。時間をおいて再試行してください。')
        page, quote = matches[0]
        stamp = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
        source = dict(title=page['title'], url=page['url'])
        self.last_evidence_items = [dict(page=page, excerpts=[quote])]
        self.last_evidence_urls = {page['url']}
        self.followup_seen_urls = {page['url']}
        self.last_research_request = question
        self.research_source_snapshot = dict(question=question, time=stamp, sources=[source])
        answer = ('【'+page['title']+'の紹介】\n取得した紹介文：\n「'+quote+'」\n\n'
                  '出典：Wikipedia（二次資料）\n'+page['url']+'\n取得：'+stamp+
                  '\n紹介文の引用です。現在の肩書や内容を公式資料で照合したわけではありません。')
        try:
            self.catalogue.learn(self.last_evidence_items)
            self.research_journal.append(question, '選択設定：Wikipedia（人物名一致・冒頭紹介）', [source])
        except (ValueError, OSError):
            answer += '\n資料または調査履歴を保存できませんでした。'
        return self.save_answer(question, answer)
