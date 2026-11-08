from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import tomeris_history_search as search

class ConversationSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=search.DesktopService(self.tmp.name,demo=True)
        self.service.store.data['conversations']=[
            {'timestamp':'2026-10-25T10:00:00+09:00','user':'今日の計画を考えたい','tomeris':'まず5分から始めましょう。'},
            {'timestamp':'2026-10-26T10:00:00+09:00','user':'Ｐｙｔｈｏｎ の使い方','tomeris':'Windowsで実行できます。'},
            {'timestamp':'2026-10-27T10:00:00+09:00','user':'休憩の工夫','tomeris':'通知を切って集中する。'},
            {'timestamp':'2026-10-27T11:00:00+09:00','user':'記号 .* の意味','tomeris':'文字をそのまま探す。'}]
        self.service.store.save(); self.before=self.service.memory_path.read_bytes()
    def tearDown(self):
        self.assertEqual(self.before,self.service.memory_path.read_bytes())
        self.service.close(); self.tmp.cleanup()
    def test_question_answer_and_multiple_terms(self):
        self.assertEqual(self.service.find_conversations('今日 計画')['total'],1)
        self.assertEqual(self.service.find_conversations('計画 5分')['total'],1)
        self.assertEqual(self.service.find_conversations('集中')['rows'][0]['user'],'休憩の工夫')
        self.assertEqual(self.service.find_conversations('計画 不在')['total'],0)
    def test_unicode_case_and_literal_symbols(self):
        self.assertEqual(self.service.find_conversations('python WINDOWS')['total'],1)
        self.assertEqual(self.service.find_conversations('.*')['total'],1)
    def test_empty_newest_first_and_isolation(self):
        result=self.service.find_conversations('　 ')
        self.assertEqual(result['total'],4); self.assertEqual(result['rows'][0]['index'],3)
        result['rows'][0]['user']='changed'
        self.assertEqual(self.service.find_conversations('.*')['rows'][0]['user'],'記号 .* の意味')
    def test_pages_no_gaps_or_duplicates(self):
        self.service.store.data['conversations']=[{'user':f'質問{i}','tomeris':'回答'} for i in range(103)]
        pages=[self.service.find_conversations('',offset) for offset in (0,50,100)]
        self.assertEqual([len(p['rows']) for p in pages],[50,50,3])
        ids=[r['index'] for p in pages for r in p['rows']]
        self.assertEqual(ids,list(reversed(range(103))))
        self.assertEqual(self.service.find_conversations('',999)['offset'],100)
    def test_invalid_query_and_malformed_records(self):
        for query,offset in [('あ'*201,0),(None,0),('',-1),('',True)]:
            with self.assertRaises(ValueError): self.service.find_conversations(query,offset)
        self.service.store.data['conversations'].extend([None,{},123,{'user':None,'tomeris':[]}])
        self.assertEqual(self.service.find_conversations()['total'],4)

if __name__=='__main__': unittest.main()
