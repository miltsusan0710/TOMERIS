import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tomeris_evidence_report_v0261 as report
from tomeris_strict_evidence import terms,passages,matches

BAD='韓国 シャインマスカット価格急落\n阪神ドラ3常深 珍しい名字に悩み\n1シャインマスカット国際/国際総合\nマンガもお得にPayPayで ebookjapan\nマンション・一戸建ての住宅情報 Yahoo!不動産'
GOOD='アイアンマンについての説明が、このページの本文に記載されています。'
class StrictEvidenceTests(unittest.TestCase):
    def test_exact_user_failure_has_no_matching_passages(self):
        self.assertEqual(passages(dict(text=BAD),'アイアンマンについて調べて'),[])
        self.assertFalse(matches('シャインマスカットとマンション',terms('アイアンマン')))
    def test_complete_names_and_aliases(self):
        self.assertTrue(matches('Iron Man appears in this example.',terms('アイアンマン')))
        self.assertFalse(matches('A man appeared here.',terms('アイアンマン')))
        self.assertFalse(matches('アイアンマンションについて',terms('アイアンマン')))
    def test_title_does_not_make_unrelated_quote_relevant(self):
        page=dict(title='アイアンマン',text=BAD)
        self.assertEqual(passages(page,'アイアンマン'),[])
    def test_relevant_and_unrelated_neighbor_are_not_joined(self):
        result=passages(dict(text=GOOD+'\n'+BAD),'アイアンマン')
        self.assertEqual(result,[GOOD])
    def test_every_required_subject_must_match(self):
        self.assertFalse(matches('アイアンマンの説明です。',terms('アイアンマン JARVIS')))
        self.assertTrue(matches('アイアンマンとジャービスの説明です。',terms('アイアンマン JARVIS')))
    def test_unrelated_results_do_not_call_summarizer_or_save_report(self):
        with TemporaryDirectory() as folder:
            s=report.DesktopService(folder,demo=True);s.demo=False;s.model_names=['test']
            try:
                before=s.memory_path.read_bytes()
                rows=[dict(title=title,url=url,snippet=BAD) for title,url in [('Yahoo! JAPAN','https://www.yahoo.co.jp/'),('Yahoo!ニュース','https://news.yahoo.co.jp/'),('乗換案内','https://transit.yahoo.co.jp/')]]
                def page(url):return dict(url=url,title='Yahoo!',text=BAD,published='')
                with patch.object(report,'search_web',return_value=rows),patch.object(report,'fetch_page',side_effect=page),patch('tomeris_grounded_summary.LocalProvider') as model:
                    answer=s.web_chat('アイアンマンについて調べて','test',automatic=True)
                    model.assert_not_called();self.assertIn('根拠を取得できません',answer)
                    for wrong in ['アメリカの漫画家','シャインマスカット','【資料に基づく整理','【対象語が含まれる本文']:
                        self.assertNotIn(wrong,answer)
                self.assertEqual(before,s.memory_path.read_bytes())
            finally:s.close()
    def test_relevant_report_is_extract_only_even_with_model(self):
        with TemporaryDirectory() as folder:
            s=report.DesktopService(folder,demo=True);s.demo=False;s.model_names=['test']
            try:
                row=dict(title='資料',url='https://example.com/',snippet=GOOD)
                with patch.object(report,'search_web',return_value=[row]),patch.object(report,'fetch_page',return_value=dict(row,text=GOOD,published='')),patch('tomeris_grounded_summary.LocalProvider') as model:
                    answer=s.research('アイアンマン','test');model.assert_not_called()
                    self.assertIn(GOOD,answer);self.assertIn('自動要約は停止',answer)
            finally:s.close()
