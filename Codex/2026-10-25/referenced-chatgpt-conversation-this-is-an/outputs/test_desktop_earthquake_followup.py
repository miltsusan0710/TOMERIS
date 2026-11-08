import unittest
from unittest.mock import patch
from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path
import xml.etree.ElementTree as E
import tomeris_earthquake_followup as q
from tomeris_desktop_v036 import DesktopService
NOW=datetime(2026,10,29,0,10,tzinfo=q.JST)
A='20261029000759';B='20261029000859'
def report(event=A,kind='発表',place='',minute='09',status='通常'):
 return E.fromstring(f'<Report><Control><Title>震源・震度に関する情報</Title><Status>{status}</Status></Control><Head><EventID>{event}</EventID><InfoType>{kind}</InfoType><ReportDateTime>2026-10-29T00:{minute}:00+09:00</ReportDateTime><TargetDateTime>2026-10-29T00:07:00+09:00</TargetDateTime></Head><Body><Earthquake><OriginTime>2026-10-29T00:07:00+09:00</OriginTime><Hypocenter><Area><Name>{place}</Name></Area></Hypocenter></Earthquake></Body></Report>')
def feed(names=('a',)):
 return E.fromstring('<feed><updated>2026-10-29T00:10:00+09:00</updated>'+''.join(f'<entry><title>震源・震度に関する情報</title><updated>2026-10-29T00:09:{59-i:02}+09:00</updated><link href="https://www.data.jma.go.jp/developer/xml/data/{name}.xml"/></entry>' for i,name in enumerate(names))+'</feed>')
def get(previous=None,**kw):
 with patch.object(q,'read_xml',side_effect=[feed(),report(**kw)]):return q.snapshot(previous,NOW)
class EarthquakeFollowupTests(unittest.TestCase):
 def test_flash_then_same_event_source_and_correction(self):
  first=get(minute='08');self.assertIn('未確認',q.render(first))
  second=get(first,place='試験震源地');self.assertIn('同じ地震',q.render(second,first));self.assertIn('試験震源地',q.render(second,first))
  third=get(second,kind='訂正',place='訂正地',minute='10');answer=q.render(third,second);self.assertIn('訂正された',answer);self.assertNotIn('試験震源地',answer)
 def test_other_earthquake_is_skipped_not_substituted(self):
  previous=get(minute='08')
  with patch.object(q,'read_xml',side_effect=[feed(('b','a')),report(event=B),report(place='同じ地震')]):
   result=q.snapshot(previous,NOW);self.assertEqual(result['event_id'],A)
  with patch.object(q,'read_xml',side_effect=[feed(),report(event=B)]),self.assertRaises(q.EarthquakeError):q.snapshot(previous,NOW)
 def test_cancellation_has_no_old_source_and_no_regression(self):
  first=get(place='旧テスト震央',minute='08');cancel=get(first,kind='取消')
  answer=q.render(cancel,first);self.assertIn('取消',answer);self.assertNotIn('旧テスト震央',answer)
  with self.assertRaises(q.EarthquakeError):get(cancel,place='旧テスト震央',minute='08')
  with self.assertRaises(q.EarthquakeError):get(cancel,place='旧テスト震央',minute='09')
 def test_training_missing_id_and_old_origin_rejected(self):
  for r in (report(status='訓練'),report(event=''),E.fromstring(E.tostring(report()).decode().replace('2026-10-29T00:07','2011-03-11T00:07'))):
   with patch.object(q,'read_xml',side_effect=[feed(),r]),self.assertRaises(q.EarthquakeError):q.snapshot(now=NOW)
 def test_identical_bulletin_not_claimed_new(self):
  first=get();again=get(first);self.assertIn('新しい発表は取得していません',q.render(again,first))
 def test_bounded_six_downloads(self):
  first=get()
  with patch.object(q,'read_xml',side_effect=[feed(tuple(str(i) for i in range(20)))]+[report(event=B)]*6) as read,self.assertRaises(q.EarthquakeError):q.snapshot(first,NOW)
  self.assertEqual(read.call_count,7)
 def test_service_followup_and_topic_reset(self):
  with TemporaryDirectory() as folder:
   s=DesktopService(Path(folder),demo=True);s.demo=False
   try:
    first=get();second=get(first,place='対象震源')
    with patch.object(q,'snapshot',side_effect=[first,second]) as fetch:
     s.web_chat('今の地震の震源は？','missing',automatic=True)
     answer=s.web_chat('その後は？','missing',automatic=True);self.assertIn('対象震源',answer);self.assertEqual(fetch.call_args.args[0]['event_id'],A)
    s.web_chat('計算: 1+2','missing',automatic=True);self.assertIsNone(s.earthquake_record)
    self.assertIn('確認した地震がありません',s.web_chat('地震の続報は？','missing',automatic=True))
   finally:s.close()
 def test_failure_does_not_reprint_last_source(self):
  with TemporaryDirectory() as folder:
   s=DesktopService(Path(folder),demo=True);s.demo=False
   try:
    s.earthquake_record=get(place='前回だけの震源')
    with patch.object(q,'snapshot',side_effect=q.EarthquakeError('通信失敗')):
     answer=s.web_chat('続報は？','missing',automatic=True);self.assertIn('未確認',answer);self.assertNotIn('前回だけの震源',answer)
   finally:s.close()

