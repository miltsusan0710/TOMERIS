from pathlib import Path
p=Path('outputs/tomeris_research_history_service.py')
s=p.read_text(encoding='utf-8').replace('from tomeris_research_journal import ResearchJournal','from tomeris_research_journal import ResearchJournal\nfrom tomeris_auto_research_v029 import instruction')
s=s.replace('answer=super().report(question,progress,model)','selected=instruction(question)[0] or getattr(self,"pending_method",None) or self.methods.mode\n        answer=super().report(question,progress,model)',1)
s=s.replace("str(self.methods.mode)","str(selected)")
Path('outputs/tomeris_research_history_v044.py').write_text(s,encoding='utf-8')
