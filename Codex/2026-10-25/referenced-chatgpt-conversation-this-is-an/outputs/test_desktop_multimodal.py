import unittest,json,subprocess,threading
from datetime import datetime,timezone,timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock,patch
from tomeris_multimodal import image_answer,speech
from tomeris_provider import ProviderError
from tomeris_multimodal_ui import plan_requests,run_requests
from tomeris_collection_rotation import DesktopService,LIMIT

class MultimediaTests(unittest.TestCase):
 def test_image_local_payload_and_completion(self):
  with TemporaryDirectory() as d:
   p=Path(d)/'x.png';p.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
   provider=Mock();provider._request.side_effect=[{'capabilities':['vision']},{'done':True,'message':{'content':'赤い四角'}}]
   self.assertIn('赤い四角',image_answer(p,'何色？','vision',provider))
   payload=provider._request.call_args.args[1];self.assertEqual(len(payload['messages']),2);self.assertIn('images',payload['messages'][1]);self.assertNotIn(str(p),str(payload))
   provider._request.side_effect=[{'capabilities':['completion']}]
   with self.assertRaises(ValueError):image_answer(p,'何色？','text',provider)
   provider._request.side_effect=[{'capabilities':['vision']},{'done':True,'done_reason':'length','message':{'content':'partial'}}]
   with self.assertRaises(ProviderError):image_answer(p,'何色？','vision',provider)
 def test_bad_image_never_sent(self):
  with TemporaryDirectory() as d:
   p=Path(d)/'x.png';p.write_bytes(b'not an image');provider=Mock()
   with self.assertRaises(ValueError):image_answer(p,'説明','v',provider)
   provider._request.assert_not_called()
 def test_speech_timeout_and_data_not_code(self):
  with patch('tomeris_multimodal.subprocess.run') as run:
   run.return_value=Mock(stdout=json.dumps({'text':'ok'}),returncode=0)
   speech('speak','$(malicious)');self.assertNotIn('$(malicious)',str(run.call_args.args));self.assertIn('$(malicious)',run.call_args.kwargs['input'])
   run.side_effect=subprocess.TimeoutExpired('ps',20)
   with self.assertRaises(ValueError):speech('listen')
 def test_bounded_agent(self):
  plan=plan_requests('100+20\n調査: アイアンマン');self.assertEqual(plan[0][0],'計算')
  service=Mock();service.research.return_value='出典つき結果';result=run_requests(plan,service,'model')
  self.assertIn('120',result);self.assertIn('出典つき結果',result)
  for text in ('ファイルを削除','\n'.join(['1+1']*5),'計算: __import__("os")'):
   with self.assertRaises(ValueError):plan_requests(text)

class RotationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close);self.s.demo=False;self.s.auto_sources_next=0
 def test_rotation_persists_failures_and_expands(self):
  with patch('tomeris_collection_rotation.fetch_topic',side_effect=OSError('offline')) as fetch:
   for _ in range(6):self.s.auto_sources_next=0;self.s.collect_public_topic()
   names=[c.args[0] for c in fetch.call_args_list];self.assertEqual(len(names),LIMIT);self.assertEqual(len(set(names)),LIMIT)
   self.s.auto_sources_next=0;self.assertFalse(self.s.auto_sources_due())
  self.s.close();other=DesktopService(Path(self.tmp.name),demo=True)
  try:self.assertTrue(set(names).isdisjoint(other.eligible_topics()))
  finally:other.close()
 def test_stop_and_reservation_failure_no_network(self):
  with patch('tomeris_collection_rotation.fetch_topic') as fetch:
   self.s.set_auto_collection(False);self.s.collect_public_topic();fetch.assert_not_called()
   self.s.set_auto_collection(True);self.s.auto_sources_next=0
   with patch.object(self.s,'reserve_topics',side_effect=OSError('disk')):self.s.collect_public_topic()
   fetch.assert_not_called();self.assertFalse(self.s.auto_sources_enabled)
 def test_corrupt_record_preserved(self):
  self.s.close();p=Path(self.tmp.name)/'collection_rotation.json';p.write_text('[]')
  other=DesktopService(Path(self.tmp.name),demo=True)
  try:self.assertTrue(other.rotation_error);self.assertEqual(p.read_text(),'[]')
  finally:other.close()
 def test_saved_cooldown(self):
  name=self.s.all_collection_topics()[0]
  self.s.catalogue.rows=[{'title':name,'retrieved':datetime.now(timezone.utc).isoformat()}]
  self.assertNotIn(name,self.s.eligible_topics())
  self.s.catalogue.rows[0]['retrieved']=(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()
  self.assertIn(name,self.s.eligible_topics())
 def test_two_fetches_overlap_serial_save(self):
  barrier=threading.Barrier(2);owner=threading.get_ident();writes=[]
  def fetch(topic):
   barrier.wait(timeout=3)
   return {'page':{'title':topic,'url':'https://example.org/'+str(len(topic))},'excerpts':[topic+'の説明']}
  def learn(items):writes.append(threading.get_ident());return 1
  with patch('tomeris_collection_rotation.fetch_topic',side_effect=fetch),patch.object(self.s.catalogue,'learn',side_effect=learn):self.s.collect_public_topic()
  self.assertEqual(writes,[owner,owner])
