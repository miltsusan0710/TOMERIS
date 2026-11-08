from pathlib import Path
p=Path('outputs/tomeris_desktop_v027.py')
s=p.read_text(encoding='utf-8-sig').replace('tomeris_multisearch_service','tomeris_auto_research').replace('v0.27','v0.28')
Path('outputs/tomeris_desktop_v028.py').write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_methods_ui.py');s=p.read_text(encoding='utf-8-sig').replace("values=['Wikipedia", "values=(['自動'] if app.service.methods.__class__.__name__=='AutoMethods' else [])+['Wikipedia")
p.write_text(s,encoding='utf-8')
