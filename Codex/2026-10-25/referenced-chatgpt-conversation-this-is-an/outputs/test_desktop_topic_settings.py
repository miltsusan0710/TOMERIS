import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_topic_settings import TopicSettings,validate_topics,DEFAULT_TOPICS,MAX_TOPIC_BYTES
class TopicSettingsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=TopicSettings(self.tmp.name)
 def test_default_does_not_create_file(self):
  self.assertEqual(self.store.load(),DEFAULT_TOPICS);self.assertFalse(self.store.path.exists())
 def test_roundtrip_and_no_alias(self):
  topics=['論理学','情報検索'];self.store.save(topics);topics.append('変更')
  self.assertEqual(TopicSettings(self.tmp.name).load(),['論理学','情報検索'])
 def test_bounds_and_url_rejected(self):
  for topics in ('abc',[],['a']*4,['x'*81],['https://example.com'],['www.example.com'],['a\nb'],[' a']):
   with self.assertRaises(ValueError):validate_topics(dict(version=1,topics=topics))
 def test_duplicate_and_wrong_version(self):
  with self.assertRaises(ValueError):validate_topics(dict(version=1,topics=['AI','ai']))
  with self.assertRaises(ValueError):validate_topics(dict(version=True,topics=['AI']))
 def test_corrupt_file_preserved(self):
  self.store.path.write_bytes(b'{oops')
  with self.assertRaises(ValueError):self.store.save(['論理学'])
  self.assertEqual(self.store.path.read_bytes(),b'{oops')
 def test_size_limit(self):
  self.store.path.write_bytes(b' '*(MAX_TOPIC_BYTES+1))
  with self.assertRaises(ValueError):self.store.load()
 def test_io_failure_preserves_prior(self):
  self.store.save(['論理学']);before=self.store.path.read_bytes()
  with patch('tomeris_topic_settings.os.replace',side_effect=OSError('test')):
   with self.assertRaises(OSError):self.store.save(['情報検索'])
  self.assertEqual(self.store.path.read_bytes(),before);self.assertEqual(list(Path(self.tmp.name).glob('*.tmp')),[])
