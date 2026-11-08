import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from datetime import datetime
import xml.etree.ElementTree as ET
import tomeris_earthquake as quake
from tomeris_source_catalogue import Catalogue
from tomeris_research_learning import DesktopService
import tomeris_evidence_v029 as evidence
import tomeris_search_methods as providers
from test_desktop_research_continuation import ROWS,page
NOW=datetime(2026,10,29,0,10,tzinfo=quake.JST)
FEED='<feed><updated>2026-10-29T00:09:40+09:00</updated><entry><title>震度速報</title><updated>2026-10-29T00:09:28+09:00</updated><link href="https://www.data.jma.go.jp/developer/xml/data/test.xml"/></entry></feed>'
REPORT='<Report><Control><Title>震度速報</Title><Status>通常</Status></Control><Head><ReportDateTime>2026-10-29T00:09:00+09:00</ReportDateTime><TargetDateTime>2026-10-29T00:07:00+09:00</TargetDateTime><InfoType>発表</InfoType></Head></Report>'
class QuakeLearningTests(unittest.TestCase):
    def test_shindo_flash_does_not_invent_epicenter(self):
        with patch.object(quake,'read_xml',side_effect=[ET.fromstring(FEED),ET.fromstring(REPORT)]) as read:
            answer=quake.fetch_latest(NOW)
            self.assertIn('震源地：この発表では未確認',answer);self.assertEqual(read.call_count,2)
    def test_stale_cancelled_training_future_refused(self):
        for report in (REPORT.replace('通常','訓練'),REPORT.replace('発表','取消'),REPORT.replace('00:07:00','01:07:00'),REPORT.replace('2026-10-29T00:07','2011-03-11T00:07')):
            with patch.object(quake,'read_xml',side_effect=[ET.fromstring(FEED),ET.fromstring(report)]),self.assertRaises(quake.EarthquakeError):quake.fetch_latest(NOW)
        with patch.object(quake,'read_xml',return_value=ET.fromstring(FEED.replace('00:09:40','00:00:00'))),self.assertRaises(quake.EarthquakeError):quake.fetch_latest(datetime(2026,10,29,1,tzinfo=quake.JST))
    def test_guard_does_not_search_wikipedia(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                with patch('tomeris_research_learning.fetch_latest',side_effect=quake.EarthquakeError('接続失敗')),patch.object(providers,'wikipedia_search') as wiki:
                    answer=s.web_chat('今の地震の震源は？','none',automatic=True);self.assertIn('未確認',answer);wiki.assert_not_called()
            finally:s.close()
        self.assertFalse(quake.recent_earthquake('2011年の地震について調べて'))
    def test_source_learning_restart_stop_clear(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(providers,'wikipedia_search',return_value=ROWS),patch.object(evidence,'wikipedia_page',side_effect=page):
                    answer=s.report('アイアンマン');self.assertIn('未検証資料を2件保存',answer)
                self.assertEqual(len(s.catalogue.rows),2)
            finally:s.close()
            s=DesktopService(folder,demo=True)
            try:
                self.assertEqual(len(s.catalogue.rows),2)
                self.assertIn('2件',s.chat('学習した資料を見せて','none'))
                s.chat('ネット学習を停止','none');self.assertFalse(s.catalogue.enabled);self.assertEqual(s.catalogue.candidates('アイアンマン'),[])
                s.chat('学習した資料を消去','none');self.assertEqual(s.catalogue.rows,[])
            finally:s.close()
    def test_corrupt_catalogue_preserved(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'research_sources.json';path.write_text('broken',encoding='utf-8')
            c=Catalogue(Path(folder));self.assertFalse(c.enabled)
            with self.assertRaises(ValueError):c.save([],True)
            self.assertEqual(path.read_text(),'broken')
    def test_known_sources_refetched_not_answered_from_cache(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                s.catalogue.learn([dict(page=page(ROWS[0]),excerpts=['アイアンマンの古い記録です。'])])
                with patch.object(providers,'wikipedia_search',return_value=[]),patch.object(providers,'search_web',return_value=[]),patch.object(evidence,'fetch_page',side_effect=evidence.PageError('通信不可')) as read:
                    answer=s.report('アイアンマン');read.assert_called_once();self.assertNotIn('古い記録です',answer);self.assertIn('本文根拠を取得できません',answer)
            finally:s.close()
    def test_current_news_never_falls_back_to_wikipedia(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True)
            try:
                with patch('tomeris_research_learning.search_web',return_value=[]),patch.object(providers,'wikipedia_search') as wiki:
                    rows,notes=s.methods.candidates('今のニュース');self.assertEqual(rows,[]);wiki.assert_not_called()
            finally:s.close()
    def test_confirmed_epicenter_uses_event_time(self):
        report=REPORT.replace('</Report>','<Body><Earthquake><OriginTime>2026-10-29T00:07:00+09:00</OriginTime><Hypocenter><Area><Name>テスト震源地</Name></Area></Hypocenter></Earthquake></Body></Report>')
        with patch.object(quake,'read_xml',side_effect=[ET.fromstring(FEED),ET.fromstring(report)]):
            answer=quake.fetch_latest(NOW);self.assertIn('震源地：テスト震源地',answer);self.assertIn('対象時刻：2026-10-29 00:07:00',answer)
