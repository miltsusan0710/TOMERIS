from pathlib import Path
import subprocess,sys
for source,old in [('check_completion_ui.py','v011'),('check_history_ui.py','v012'),('check_google_ui.py','v010')]:
    path=Path('work')/source
    test=Path('work')/('v013_'+source)
    test.write_text(path.read_text(encoding='utf-8-sig').replace('tomeris_desktop_'+old,'tomeris_desktop_v013'),encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(test)],check=True)
