from pathlib import Path
s=Path('outputs/tomeris_desktop_v0232.py').read_text(encoding='utf-8-sig').replace('v0.23.2','v0.24')
s=s.replace('from tomeris_weather_followup import DesktopService as PlanService','from tomeris_capabilities import DesktopService as PlanService')
s=s.replace("'ネット検索','2モデル比較'","'ネット検索','情報収集','2モデル比較'")
s=s.replace("        elif self.mode.get() in ('会話＋自動検索','ネット検索'):","        elif self.mode.get()=='情報収集':\n            func=lambda:self.service.research(question,model,lambda s:self.events.put(('progress',s)))\n            label='複数の検索語で情報を集めています…'\n        elif self.mode.get() in ('会話＋自動検索','ネット検索'):")
s=s.replace("self.mode.get()!='ネット検索'","self.mode.get() not in ('ネット検索','情報収集')")
s=s.replace("self.mode.get() in ('会話＋自動検索','ネット検索') and not self.busy","self.mode.get() in ('会話＋自動検索','ネット検索','情報収集') and not self.busy")
s=s.replace('こんにちは。質問や相談を入力してください。','こんにちは。直前の2往復を踏まえて会話します。計算は「計算: (1200 + 800) * 1.1」、情報収集は「調査: Ollama」のように入力してください。')
Path('outputs/tomeris_desktop_v024.py').write_text(s,encoding='utf-8')
# Include explicit research prefix in automatic routing.
p=Path('outputs/tomeris_capabilities.py');s=p.read_text(encoding='utf-8-sig').replace("bool(re.search(r'情報収集|調査して|詳しく調べて|比較して調べ',text))","bool(re.search(r'情報収集|調査して|詳しく調べて|比較して調べ|^調査[:：]',text))")
p.write_text(s,encoding='utf-8')
