"""Prefer a matching encyclopedia article's lead for simple overview requests."""
import re
from tomeris_name_punctuation import DesktopService as BaseService, comparable, passages


def key(text):
    return re.sub(r'\s+', '', comparable(text)).casefold()


def overview_subject(question):
    match = re.fullmatch(r'([^\s:：/]{1,40})について調べて[。！？!?]*', question.strip())
    if not match or re.search(r'最新|今日|現在|ニュース|価格|比較|違い|方法|詳しく', match[1]):
        return None
    return match[1]


class OverviewMethods:
    def __init__(self, base):
        object.__setattr__(self, '_base', base)

    def __getattr__(self, name):
        return getattr(self._base, name)

    def __setattr__(self, name, value):
        setattr(self._base, name, value)

    def candidates(self, text):
        rows, notes = self._base.candidates(text)
        subject = overview_subject(self._base.question_context)
        if self._base.mode == '自動' and subject:
            exact = [row for row in rows if row.get('wiki_id') and key(row.get('title', '')) == key(subject)]
            if exact:
                return exact, notes + ['概要のため対象名と一致する百科事典記事を優先しました。別記事の断片は混ぜていません。']
        return rows, notes


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods = OverviewMethods(self.methods)

    def extract_passages(self, page, topic):
        subject = overview_subject(self.methods.question_context)
        if subject and page.get('provider', '').startswith('Wikipedia') and key(page.get('title', '')) == key(subject):
            lead = re.split(r'\n\s*==', page['text'], maxsplit=1)[0]
            return passages(dict(page, text=lead), topic)
        return passages(page, topic)
