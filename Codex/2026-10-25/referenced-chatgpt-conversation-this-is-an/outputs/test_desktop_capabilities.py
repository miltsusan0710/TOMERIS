import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from tomeris_calculator import calculate,expression_from,CalculationError
import tomeris_capabilities as cap
import tomeris_web_search as web

class CapabilitiesTests(unittest.TestCase):
    def test_exact_calculation(self):
        for question,result in [('0.1 + 0.2','結果：0.3'),('計算: (1200 + 800) * 1.1','結果：2200'),('12000の15%','結果：1800'),('2^10','結果：1024'),('－３×４','結果：-12')]:
            self.assertIn(result,calculate(expression_from(question)))
        self.assertIn('正確な分数：1/3',calculate('1/3'))
        self.assertIsNone(expression_from('集中する工夫を3つ'))
    def test_calculator_rejects_code_and_limits(self):
        for expression in ["__import__('os').system('echo bad')",'1/0','2**101','True','[1][0]','2**(2**20)','1'*41,'1e5','1%2']:
            with self.assertRaises(CalculationError):calculate(expression)
        with self.assertRaises(CalculationError): expression_from('計算: open("a")')
    def test_bounded_conversation_prompt(self):
        turns=[('OLD','OLD'),('FIRST','A'*3000),('SECOND','B'*3000)]
        with patch.object(cap,'LocalProvider') as factory:
            factory.return_value.generate.return_value='answer'
            provider=cap.ContextProvider('test',turns)
            provider.generate([{'role':'system','content':'rules'},{'role':'user','content':'NEXT'}])
            messages=factory.return_value.generate.call_args.args[0]
            self.assertEqual(len(messages),6); self.assertEqual(messages[1]['content'],'FIRST')
            self.assertEqual(len(messages[2]['content']),1200); self.assertEqual(messages[-1]['content'],'NEXT')
    def test_calculation_offline_and_weather_followup(self):
        with TemporaryDirectory() as folder:
            s=cap.DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(web,'search_web') as search,patch.object(cap,'LocalProvider') as provider:
                    self.assertIn('結果：0.3',s.web_chat('0.1+0.2','missing',automatic=True));search.assert_not_called();provider.assert_not_called()
                with patch.object(web,'search_web',return_value=[]) as search:
                    s.web_chat('今日の天気は？','missing',automatic=True)
                    answer=s.web_chat('荒川区','missing',automatic=True)
                    search.assert_called_once_with('荒川区の今日の天気');self.assertIn('確認できません',answer)
            finally:s.close()
    def test_real_chat_receives_only_session_context(self):
        with TemporaryDirectory() as folder:
            s=cap.DesktopService(folder,demo=True);s.demo=False;s.model_names=['test']
            try:
                s.store.add_conversation('OLD_SECRET','OLD_SECRET')
                s.remember('MEMORY_SECRET','その他')
                with patch.object(cap,'LocalProvider') as provider:
                    provider.return_value.generate.return_value='FIRST_ANSWER'
                    s.chat('FIRST_QUESTION','test')
                    s.chat('それについて説明して','test')
                    prompt=str(provider.return_value.generate.call_args)
                    self.assertIn('FIRST_QUESTION',prompt);self.assertIn('FIRST_ANSWER',prompt)
                    self.assertNotIn('OLD_SECRET',prompt);self.assertNotIn('MEMORY_SECRET',prompt)
            finally:s.close()
    def test_research_sources_dedup_and_privacy(self):
        with TemporaryDirectory() as folder:
            s=cap.DesktopService(folder,demo=True);s.demo=False;s.model_names=['test']
            try:
                s.remember('SECRET','その他');s.session_turns=[('SECRET','SECRET')]
                rows=[dict(title='Ollama official',url='https://ollama.com/',snippet='Local model runner'),dict(title='Ollama documentation',url='https://docs.ollama.com/',snippet='Documentation')]
                with patch.object(cap,'search_web',return_value=rows) as search,patch.object(cap,'LocalProvider') as provider:
                    provider.return_value.generate.return_value='整理 [1]'
                    answer=s.web_chat('調査: Ollama','test',True,True)
                    self.assertEqual([c.args[0] for c in search.call_args_list],['Ollama','Ollama 公式','Ollama 注意点'])
                    self.assertNotIn('SECRET',str(provider.return_value.generate.call_args))
                    self.assertEqual(answer.count('https://ollama.com/'),1)
                    self.assertIn('ページ全文',answer); self.assertEqual(len(s.store.data['conversations']),1)
                with patch.object(cap,'search_web',side_effect=cap.SearchError('down')):
                    answer=s.research('Ollama','test');self.assertIn('取得できません',answer)
            finally:s.close()
    def test_research_partial_failure_still_returns_evidence(self):
        with TemporaryDirectory() as folder:
            s=cap.DesktopService(folder,demo=True);s.demo=False
            try:
                row=dict(title='Ollama',url='https://ollama.com/',snippet='Local models')
                with patch.object(cap,'search_web',side_effect=[cap.SearchError('down'),[row],[]]):
                    answer=s.research('Ollama','missing');self.assertIn('https://ollama.com/',answer);self.assertIn('取得失敗',answer)
            finally:s.close()
