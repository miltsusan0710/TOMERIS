from pathlib import Path
p=Path('outputs/test_desktop_evidence.py')
s=p.read_text(encoding='utf-8-sig')
s+='''
    def test_direct_url_bypasses_search_and_keeps_source(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(reports,'search_web') as search,patch.object(reports,'fetch_page',return_value=PAGE) as fetch:
                    answer=s.web_chat('https://docs.ollama.com/ 内容を教えて','missing',automatic=True)
                    search.assert_not_called();fetch.assert_called_once_with('https://docs.ollama.com/')
                    self.assertIn(PAGE['url'],answer)
            finally:s.close()
    def test_invalid_summary_is_not_displayed(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False;s.model_names=['test']
            try:
                with patch.object(reports,'search_web',return_value=[ROW]),patch.object(reports,'fetch_page',return_value=PAGE),patch.object(reports,'summarize',return_value=None):
                    answer=s.research('Ollama','test')
                    self.assertNotIn('【資料に基づく整理',answer);self.assertIn('根拠原文だけ',answer)
            finally:s.close()
'''
p.write_text(s,encoding='utf-8')
