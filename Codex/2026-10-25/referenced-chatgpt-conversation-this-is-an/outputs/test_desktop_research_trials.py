import json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_research_trials import collect,save_record,save_review,render

class TrialTests(unittest.TestCase):
 def rows(self):
  return [dict(title=title,url='https://ja.wikipedia.org/wiki/'+str(i),wiki_id=i+1,wiki_lang='ja') for i,title in enumerate(['解説','情報検索','検索エンジン','その他'])]
 def page(self,row):return dict(title=row['title'],url=row['url'],text='情報検索は、必要な情報を探し出すための方法として説明されています。',published='',updated='2020-01-01T00:00:00Z',provider='Wikipedia')
 def record(self):
  with patch('tomeris_research_trials.wikipedia_search',return_value=self.rows()),patch('tomeris_research_trials.wikipedia_page',side_effect=self.page):return collect('情報検索について調べて','overview')
 def test_shared_snapshot_bound_and_order(self):
  with patch('tomeris_research_trials.wikipedia_search',return_value=self.rows()) as search,patch('tomeris_research_trials.wikipedia_page',side_effect=self.page) as fetch:
   record=collect('情報検索について調べて','overview')
  search.assert_called_once_with('情報検索');self.assertEqual(fetch.call_count,3)
  self.assertEqual(record['rankings']['search_order'][0],self.rows()[0]['url']);self.assertEqual(record['rankings']['exact_title_first'][0],self.rows()[1]['url'])
  self.assertFalse(record['reviewed']);self.assertNotIn('ratings',record)
 def test_failure_preserved_not_fabricated(self):
  with patch('tomeris_research_trials.wikipedia_search',return_value=self.rows()),patch('tomeris_research_trials.wikipedia_page',side_effect=ValueError('offline')):
   record=collect('情報検索','specific')
  self.assertTrue(all(p['page'] is None and p['status']=='failed' for p in record['pages']));self.assertIn('取得失敗',render(record))
 def test_latest_and_url_rejected_before_network(self):
  with patch('tomeris_research_trials.wikipedia_search') as search:
   for query in ['最新ニュース','今の地震','https://example.com']:
    with self.assertRaises(ValueError):collect(query,'overview')
   search.assert_not_called()
 def test_review_binding_and_exclusive_snapshot(self):
  with TemporaryDirectory() as d:
   record=self.record();path=save_record(d,record);before=path.read_bytes()
   with self.assertRaises(FileExistsError):save_record(d,record)
   review=save_review(path,{'search_order':0,'exact_title_first':1},'対象名に一致する記事を確認したため。')
   result=json.loads(review.read_text(encoding='utf-8'));self.assertEqual(result['trial_id'],record['id']);self.assertFalse(result['production_enabled']);self.assertEqual(before,path.read_bytes())
   payload=json.loads(before);payload['record']['question']='改変';path.write_text(json.dumps(payload),encoding='utf-8')
   with self.assertRaises(ValueError):save_review(path,{'search_order':0,'exact_title_first':1},'比較内容を確認した。')
 def test_no_scores_without_review_and_empty_search(self):
  with TemporaryDirectory() as d:
   path=save_record(d,self.record())
   for scores,reason in [({'search_order':None,'exact_title_first':1},'適合を確認した'),({'search_order':1,'exact_title_first':1},'')]:
    with self.assertRaises(ValueError):save_review(path,scores,reason)
   with patch('tomeris_research_trials.wikipedia_search',return_value=[]):empty=collect('情報検索','overview')
   path=save_record(d,empty)
   with self.assertRaises(ValueError):save_review(path,{'search_order':-1,'exact_title_first':-1},'候補がなかったため。')
 def test_dates_not_claimed_event_time(self):
  text=render(self.record());self.assertIn('出来事の発生日時ではありません',text);self.assertIn('掲載日：不明',text);self.assertIn('2020-01-01',text)
