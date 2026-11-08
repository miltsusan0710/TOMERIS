from pathlib import Path
p=Path('outputs/tomeris_evidence_v029.py')
s=p.read_text(encoding='utf-8');s=s.replace('excerpt=passages(page,topic)',"excerpt=getattr(self, 'extract_passages', passages)(page,topic)");p.write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_desktop_v037.py')
s=p.read_text(encoding='utf-8').replace('v0.37','v0.38').replace('from tomeris_context_boundaries import','from tomeris_prose_evidence import')
Path('outputs/tomeris_desktop_v038.py').write_text(s,encoding='utf-8')
