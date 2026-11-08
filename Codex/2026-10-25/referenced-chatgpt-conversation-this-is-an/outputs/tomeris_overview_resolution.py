"""Use provider-declared title redirects, never fuzzy identity guesses."""
from urllib.parse import urlencode, quote
from tomeris_search_methods import json_request, MethodError
from tomeris_overview import overview_subject, key

def resolve_title(subject):
    data = json_request('https://ja.wikipedia.org/w/api.php?'+urlencode(dict(
        action='query', titles=subject, redirects=1, prop='pageprops',
        ppprop='disambiguation', format='json', formatversion=2)))
    pages = data.get('query', {}).get('pages', [])
    if len(pages) != 1:
        return None
    page = pages[0]
    if 'missing' in page or 'disambiguation' in page.get('pageprops', {}):
        return None
    if type(page.get('pageid')) is not int or page['pageid'] <= 0 or not page.get('title'):
        return None
    return dict(title=page['title'], wiki_id=page['pageid'], wiki_lang='ja',
                url='https://ja.wikipedia.org/wiki/'+quote(page['title'].replace(' ', '_'), safe=''),
                snippet='', provider='Wikipedia ja', requested_title=subject)

class ResolvedMethods:
    def __init__(self, base):
        object.__setattr__(self, '_base', base)
        object.__setattr__(self, 'resolved', None)
    def __getattr__(self, name):return getattr(self._base, name)
    def __setattr__(self, name, value):
        if name == 'resolved':object.__setattr__(self, name, value)
        else:setattr(self._base, name, value)
    def candidates(self, text):
        self.resolved = None
        subject = overview_subject(self.question_context)
        if self.mode == '自動' and subject:
            try:row = resolve_title(subject)
            except (MethodError, OSError):row = None
            if row:
                self.resolved = row
                return [row], ['Wikipediaの指定記事・転送先を確認：'+subject+' → '+row['title']]
        rows, notes = self._base.candidates(text)
        if self.mode == '自動' and subject:
            rows = [row for row in rows if not row.get('wiki_id') or key(row['title']) == key(subject)]
        return rows, notes
