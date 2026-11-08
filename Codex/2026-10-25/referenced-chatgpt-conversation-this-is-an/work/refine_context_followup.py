from pathlib import Path
p=Path('outputs/tomeris_context_boundaries.py');s=p.read_text(encoding='utf-8')
s=s.replace("        if selected:\n            # A new named provider", "        if selected and more_information(topic) and self.last_research_request:\n            self.pending_method=None;self.pending_subject=False;self.pending_weather=None;self.last_weather_place=None;self.earthquake_record=None\n            return text,None\n        if selected:\n            # A new named provider")
p.write_text(s,encoding='utf-8')
