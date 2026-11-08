import unittest,json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from tomeris_desktop_v035 import DesktopService
from tomeris_source_management import CheckedCatalogue
from tomeris_page_reader import PageError
from test_desktop_source_backup import ROW

class SourceManagementTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.s=DesktopService(Path(self.tmp.name)/'data',demo=True)
        self.addCleanup(self.tmp.cleanup);self.addCleanup(self.s.close)
        self.other=dict(ROW,url='https://example.com/second',title='別の資料')
        self.s.catalogue.save([ROW,self.other],False)
    def test_search_and_isolated_delete_persist(self):
        result=self.s.source_records('テスト');self.assertEqual(len(result['rows']),1)
        row=result['rows'][0];self.s.remove_source(row['url'],row['revision'])
        self.assertEqual(self.s.catalogue.rows,[self.other]);self.assertFalse(self.s.catalogue.enabled)
        self.assertEqual(CheckedCatalogue(self.s.data_dir).rows,[self.other])
    def test_revision_prevents_stale_delete(self):
        row=self.s.source_records('テスト')['rows'][0]
        self.s.catalogue.save([dict(ROW,excerpt='変更済み'),self.other],False)
        with self.assertRaises(ValueError):self.s.remove_source(row['url'],row['revision'])
        self.assertEqual(len(self.s.catalogue.rows),2)
    def test_failed_write_keeps_file_and_rows(self):
        row=self.s.source_records('テスト')['rows'][0];before=self.s.catalogue.path.read_bytes()
        with patch('tomeris_source_catalogue.os.replace',side_effect=OSError('test')),self.assertRaises(OSError):self.s.remove_source(row['url'],row['revision'])
        self.assertEqual(self.s.catalogue.path.read_bytes(),before);self.assertEqual(len(self.s.catalogue.rows),2)
    def test_success_and_failed_retrieval_do_not_modify_evidence(self):
        self.s.demo=False;row=self.s.source_records('テスト')['rows'][0];before=self.s.catalogue.path.read_bytes()
        with patch('tomeris_source_management.fetch_page',return_value=dict(url=ROW['url'],text='新しく取得した本文')) as fetch:
            self.assertIn('再取得成功',self.s.check_source(row['url'],row['revision']));fetch.assert_called_once_with(ROW['url'])
        with patch('tomeris_source_management.fetch_page',side_effect=PageError('取得不可')):
            self.assertIn('再取得失敗',self.s.check_source(row['url'],row['revision']))
        self.assertEqual(before,self.s.catalogue.path.read_bytes());self.assertIn('再取得失敗',self.s.source_records('テスト')['rows'][0]['check'])
    def test_invalid_catalogue_preserved_without_overwrite(self):
        path=self.s.catalogue.path;bad=dict(version=1,enabled=True,rows=[dict(ROW,retrieved='invalid')]);path.write_text(json.dumps(bad),encoding='utf-8');before=path.read_bytes()
        loaded=CheckedCatalogue(self.s.data_dir);self.assertTrue(loaded.error);self.assertFalse(loaded.enabled)
        with self.assertRaises(ValueError):loaded.save([],True)
        self.assertEqual(before,path.read_bytes())
    def test_backup_of_latest_service_preserves_source_support(self):
        target=Path(self.tmp.name)/'backup.zip';self.s.export_backup(target)
        self.assertEqual(self.s.inspect_backup(target)['counts']['research_sources'],2)
