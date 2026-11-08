import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tomeris_auto_research_v029 as routing
import tomeris_evidence_v029 as evidence
import tomeris_search_methods as providers

ROWS=[dict(title='アイアンマン '+str(i),url='https://ja.wikipedia.org/wiki/'+str(i),snippet='アイアンマン',wiki_id=i,wiki_lang='ja') for i in range(1,6)]
def page(row):return dict(title=row['title'],url=row['url'],text='アイアンマンの資料'+str(row['wiki_id'])+'に書かれた独自の説明をここで確認しています。',published='')
class ContinuationTests(unittest.TestCase):
    def service(self):
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup)
        service=routing.DesktopService(folder.name,demo=True);service.demo=False;self.addCleanup(service.close);return service
    def test_followup_fetches_new_sources_and_exhaustion(self):
        s=self.service()
        with patch.object(providers,'wikipedia_search',return_value=ROWS) as search,patch.object(evidence,'wikipedia_page',side_effect=page) as read:
            first=s.web_chat('アイアンマンについて調べて','missing',automatic=True)
            second=s.web_chat('他の情報は？','missing',automatic=True)
            self.assertIn('資料1',first);self.assertIn('資料3',second);self.assertNotIn('資料1',second)
            third=s.web_chat('もっと詳しく','missing',automatic=True);self.assertIn('資料5',third)
            fourth=s.web_chat('ほかには？','missing',automatic=True);self.assertIn('追加の本文根拠を取得できません',fourth)
            self.assertEqual(read.call_count,5)
            self.assertTrue(all(call.args[0]=='アイアンマン' for call in search.call_args_list))
    def test_explicit_method_is_kept(self):
        s=self.service();s.methods.brave_key='TEST'
        with patch.object(providers,'wikipedia_search',return_value=ROWS) as wiki,patch.object(providers,'brave_search') as brave,patch.object(evidence,'wikipedia_page',side_effect=page):
            s.web_chat('Wikipediaでアイアンマンについて調べて','missing',automatic=True)
            s.web_chat('他の情報は？','missing',automatic=True);brave.assert_not_called();self.assertEqual(wiki.call_count,2)
    def test_no_context_does_not_guess(self):
        s=self.service()
        with patch.object(providers,'wikipedia_search') as search:
            self.assertIn('対象を教えて',s.web_chat('他の情報は？','missing',automatic=True));search.assert_not_called()
    def test_new_topic_clears_sources(self):
        s=self.service()
        with patch.object(providers,'wikipedia_search',return_value=ROWS),patch.object(evidence,'wikipedia_page',side_effect=page):
            s.report('アイアンマン');s.report('Ollama')
            self.assertIsNone(s.last_research_request)
            self.assertFalse(s.followup_seen_urls)
    def test_redirect_to_seen_source_is_not_repeated(self):
        s=self.service()
        with patch.object(providers,'wikipedia_search',return_value=ROWS),patch.object(evidence,'wikipedia_page',side_effect=lambda row:page(ROWS[0])):
            s.report('アイアンマン');answer=s.web_chat('他の情報は？','missing',automatic=True)
            self.assertIn('追加の本文根拠を取得できません',answer)
