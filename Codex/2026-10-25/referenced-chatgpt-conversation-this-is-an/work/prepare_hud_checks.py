from pathlib import Path
s=Path('work/check_followup_chat_ui.py').read_text(encoding='utf-8-sig').replace('v029','v030');Path('work/check_hud_chat_ui.py').write_text(s,encoding='utf-8')
s=Path('work/check_research_continuation_ui.py').read_text(encoding='utf-8-sig').replace('v029','v030');Path('work/check_hud_methods_ui.py').write_text(s,encoding='utf-8')
