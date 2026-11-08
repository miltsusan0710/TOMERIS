import unittest,json
from pathlib import Path
from tempfile import TemporaryDirectory
from tomeris_trial_dataset_ui import inventory

class InventoryTests(unittest.TestCase):
 def test_missing_folder_does_not_create_data(self):
  with TemporaryDirectory() as d:
   path=Path(d)/'missing';self.assertEqual(inventory(path),([],0));self.assertFalse(path.exists())
 def test_lists_multiple_reviews_without_choosing(self):
  with TemporaryDirectory() as d:
   root=Path(d);trial='a'*32
   (root/(trial+'.json')).write_text(json.dumps({'record':{'id':trial,'question':'公開テーマ','context':'overview'}}),encoding='utf-8')
   for i in range(2):(root/f'{trial}.review.{i}.json').write_text(json.dumps({'trial_id':trial,'reason':f'理由{i}','ratings':{'search_order':i}}),encoding='utf-8')
   rows,skipped=inventory(root);self.assertEqual(len(rows),2);self.assertEqual(skipped,0)
   self.assertTrue(all('split' not in row for row in rows))
 def test_bad_review_skipped_without_rewriting(self):
  with TemporaryDirectory() as d:
   root=Path(d);path=root/'x.review.y.json';path.write_text('bad',encoding='utf-8')
   self.assertEqual(inventory(root),([],1));self.assertEqual(path.read_text(),'bad')
 def test_path_in_record_id_is_not_opened(self):
  with TemporaryDirectory() as d:
   root=Path(d);(root/'x.review.y.json').write_text(json.dumps({'trial_id':'../private'}),encoding='utf-8')
   self.assertEqual(inventory(root),([],1))
