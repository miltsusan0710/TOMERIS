from pathlib import Path
p=Path('outputs/tomeris_evidence_report.py');s=p.read_text(encoding='utf-8-sig').replace('    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):','    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):\n        arithmetic=self.arithmetic(question)\n        if arithmetic is not None:\n            self.pending_subject=False\n            return arithmetic')
p.write_text(s,encoding='utf-8')
