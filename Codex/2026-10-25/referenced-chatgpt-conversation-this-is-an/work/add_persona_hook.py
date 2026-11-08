from pathlib import Path
p=Path('outputs/tomeris_capabilities.py');s=p.read_text(encoding='utf-8');s=s.replace('conversation_style(self.store)),self.store,query)',"conversation_style(self.store)+getattr(self,'conversation_persona',lambda text:'')(text)),self.store,query)")
p.write_text(s,encoding='utf-8')
