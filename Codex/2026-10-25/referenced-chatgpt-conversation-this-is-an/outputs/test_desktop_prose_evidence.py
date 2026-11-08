import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_prose_evidence import passages
from tomeris_desktop_v038 import DesktopService

GOOD='Ollamaはローカル環境でモデルを動かすためのツールとして説明されています。'
BAD='github.com/ollama/ollama\nollama.com テンプレートを表示\nOllama メインメニュー ページ 編集 履歴'
class ProseEvidenceTests(unittest.TestCase):
    def test_skip_ui_and_urls_then_keep_exact_prose(self):
        self.assertEqual(passages(dict(text=BAD+'\n'+GOOD),'Ollama'),[GOOD])
    def test_no_prose_means_no_evidence(self):
        self.assertEqual(passages(dict(text=BAD),'Ollama'),[])
    def test_keyword_in_url_is_not_evidence(self):
        self.assertEqual(passages(dict(text='このツールの詳細については https://example.com/ollama を参照してください。'),'Ollama'),[])
    def test_all_anchors_still_required(self):
        self.assertEqual(passages(dict(text=GOOD),'Ollama JARVIS'),[])
    def test_english_and_link_in_real_prose(self):
        sentence='Ollama is a tool described at https://example.com/docs for local models.'
        self.assertEqual(passages(dict(text=sentence),'Ollama'),[sentence])
    def test_latest_service_calls_filter_and_fails_closed(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                row=dict(title='Ollama',url='https://example.com/ollama',snippet=GOOD)
                with patch.object(s.methods,'candidates',return_value=([row],[])),patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=BAD,published='')):
                    answer=s.web_chat('Ollamaについて調べて','unused',automatic=True)
                self.assertEqual(s.last_evidence_items,[])
                self.assertNotIn('github.com/ollama',answer)
            finally:s.close()

