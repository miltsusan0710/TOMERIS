import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock,patch
import tomeris_desktop_service as desktop

class DesktopTests(unittest.TestCase):
    def test_import_preserves_original_and_does_not_reimport(self):
        with TemporaryDirectory() as folder:
            root=Path(folder); source=root/'old.json'
            raw=json.dumps({'version':3,'memories':[{'id':'M0001','category':'目標','text':'トメリスの目標は支援すること'}],'growth_log':[],'conversations':[],'decisions':[],'metadata':{'next_memory_id':2}}).encode()
            source.write_bytes(raw)
            service=desktop.DesktopService(root/'data',source)
            try:
                answer=service.chat('私の目標を教えて','not-connected',True)
                self.assertIn('M0001',answer)
                self.assertEqual(source.read_bytes(),raw)
                service.remember('私の目標は毎週読書','目標')
            finally:
                service.close()
            service=desktop.DesktopService(root/'data',source)
            try:
                self.assertFalse(service.imported)
                self.assertEqual(len(service.store.data['memories']),2)
            finally:
                service.close()
    def test_second_instance_rejected_and_lock_released(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            first=desktop.DesktopService(root,demo=True)
            try:
                with self.assertRaises(RuntimeError):
                    desktop.DesktopService(root,demo=True)
            finally:
                first.close()
            again=desktop.DesktopService(root,demo=True); again.close()
    def test_pc_and_views_never_enter_history(self):
        with TemporaryDirectory() as folder:
            service=desktop.DesktopService(folder,demo=True)
            try:
                before=service.memory_path.read_bytes()
                with patch.object(desktop,'pc_info',return_value={'test':'pc-marker'}):
                    self.assertIn('pc-marker',service.view('pc'))
                service.view('history');service.view('memories');service.view('comparisons')
                self.assertEqual(service.memory_path.read_bytes(),before)
            finally: service.close()
    def test_generation_error_does_not_save_and_ui_can_retry(self):
        with TemporaryDirectory() as folder:
            service=desktop.DesktopService(folder,source=Path(folder)/'absent')
            service.model_names=['test']
            try:
                before=service.memory_path.read_bytes()
                with patch.object(desktop.core,'generate_checked_response',side_effect=desktop.ProviderError('offline')):
                    with self.assertRaises(desktop.ProviderError):service.chat('こんにちは','test')
                self.assertEqual(service.memory_path.read_bytes(),before)
                with patch.object(desktop.core,'generate_checked_response',return_value='こんにちは'):
                    self.assertEqual(service.chat('こんにちは','test'),'こんにちは')
                self.assertEqual(len(service.store.data['conversations']),1)
            finally: service.close()
    def test_failed_save_rolls_back_memory(self):
        with TemporaryDirectory() as folder:
            service=desktop.DesktopService(folder,demo=True)
            try:
                before=deepcopy(service.store.data)
                with patch.object(service.store,'save',side_effect=OSError('disk')):
                    with self.assertRaises(OSError): service.remember('new','その他')
                self.assertEqual(service.store.data,before)
            finally: service.close()
    def test_compare_separate_storage_and_duplicate_memory(self):
        with TemporaryDirectory() as folder:
            service=desktop.DesktopService(folder,demo=True)
            try:
                service.compare('question',['a','b'],lambda s:None)
                self.assertEqual(len(service.store.data['comparisons']),1)
                self.assertEqual(service.store.data['conversations'],[])
                service.remember('目標','その他')
                self.assertIn('既に',service.remember('目 標','その他'))
                self.assertEqual(len(service.store.data['memories']),1)
            finally:service.close()

if __name__=='__main__':unittest.main()
