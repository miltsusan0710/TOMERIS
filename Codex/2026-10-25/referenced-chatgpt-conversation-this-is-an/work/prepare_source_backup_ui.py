from pathlib import Path
s=Path('work/check_restore_ui.py').read_text(encoding='utf-8-sig').replace('tomeris_desktop_v017','tomeris_desktop_v034').replace('from tomeris_restore import DesktopService','from tomeris_desktop_v034 import DesktopService').replace('tomeris_restore_ui.','tomeris_restore_ui_v034.')
s=s.replace("    archive=parent/'backup.zip';", "    service.catalogue.save([dict(url='https://example.com/article',title='テスト資料',excerpt='未検証の引用',retrieved='2026-10-29T01:00:00+09:00')],False)\n    archive=parent/'backup.zip';")
s=s.replace("    panel.window.geometry('600x500');", "    assert '保存資料 1件 / 資料学習：停止' in panel.body.get('1.0','end')\n    panel.window.geometry('600x500');")
Path('work/check_source_backup_ui.py').write_text(s,encoding='utf-8')
