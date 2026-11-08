from pathlib import Path
p=Path('outputs/tomeris_evidence_v029.py');s=p.read_text(encoding='utf-8');b=p.with_name('tomeris_evidence_v029_before_v033.py')
if not b.exists():b.write_text(s,encoding='utf-8')
s=s.replace('        self.last_evidence_urls=set()', '        self.last_evidence_urls=set();self.last_evidence_items=[]',1).replace('        if failures:answer+=', '        self.last_evidence_items=checked\n        if failures:answer+=');p.write_text(s,encoding='utf-8')
s=Path('outputs/tomeris_desktop_v032.py').read_text(encoding='utf-8').replace('from tomeris_conversation_preferences import','from tomeris_research_learning import').replace('v0.32','v0.33')
Path('outputs/tomeris_desktop_v033.py').write_text(s,encoding='utf-8')
