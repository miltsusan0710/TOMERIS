import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_name_punctuation import passages
from tomeris_desktop_v064 import DesktopService

QUOTE = 'トニー・スタークは、物語に登場する架空の人物として紹介されています。'


class NamePunctuationTests(unittest.TestCase):
    def test_missing_dot_matches_verbatim(self):
        self.assertEqual([QUOTE], passages(dict(text=QUOTE), 'トニースターク'))

    def test_query_dot_and_halfwidth_forms(self):
        raw = QUOTE.replace('トニー・スターク', 'トニースターク')
        for query in ('トニー・スターク', 'ﾄﾆｰ･ｽﾀｰｸ'):
            self.assertEqual([raw], passages(dict(text=raw), query))

    def test_no_partial_or_separated_name_match(self):
        for text in (QUOTE.replace('スターク', 'スタークス'),
                     'トニーは別の人物であり、スタークという人物とは無関係です。'):
            self.assertEqual([], passages(dict(text=text), 'トニースターク'))

    def test_url_only_and_ui_rejected(self):
        for text in ('https://example.com/トニースターク のページには別の話題が掲載されています。',
                     QUOTE+'テンプレートを表示'):
            self.assertEqual([], passages(dict(text=text), 'トニースターク'))

    def test_latest_service_report_path(self):
        with TemporaryDirectory() as tmp:
            s = DesktopService(Path(tmp), demo=True)
            try:
                s.demo = False
                row = dict(title='トニー・スターク',url='https://example.com/tony',snippet=QUOTE)
                with patch.object(s.methods,'candidates',return_value=([row],[])), patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=QUOTE,published='')):
                    answer = s.web_chat('トニースタークについて調べて','unused',automatic=True)
                self.assertIn(QUOTE,answer)
                self.assertNotIn('本文根拠未取得',answer)
            finally:
                s.close()
