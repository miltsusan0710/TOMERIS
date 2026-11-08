from pathlib import Path
p=Path('outputs/tomeris_auto_research_v029.py');s=p.read_text(encoding='utf-8')
s=s.replace("        self.last_evidence_urls=set()\n        answer=super().report(question,progress,model)","        self.last_evidence_urls=set()\n        pending=self.pending_method\n        answer=super().report(question,progress,model)")
s=s.replace("            self.last_research_request=question\n            self.followup_seen_urls", "            prefixes={'Wikipedia（日本語）':'Wikipedia','Wikipedia（英語）':'Wikipedia英語','Brave API':'Brave'}\n            self.last_research_request=(prefixes[pending]+'で'+question) if pending in prefixes and not instruction(question)[0] else question\n            self.followup_seen_urls")
p.write_text(s,encoding='utf-8')
s=Path('work/check_auto_fixes_ui.py').read_text(encoding='utf-8').replace('v0281','v029');Path('work/check_research_continuation_ui.py').write_text(s,encoding='utf-8')
