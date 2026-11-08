from pathlib import Path
root=Path('outputs')
s=(root/'tomeris_backup.py').read_text(encoding='utf-8-sig').replace("'app_version':'0.16'","'app_version':'0.17'")
s=s.replace('現時点ではアプリ内の復元ボタンはありません。復元時は既存データを別途保管してから扱ってください。','v0.17以降の「データ」メニューから、内容を検査して別フォルダーに復元できます。')
(root/'tomeris_backup_v017.py').write_text(s,encoding='utf-8')
p=root/'tomeris_restore.py'; s=p.read_text(encoding='utf-8-sig').replace('from tomeris_backup import','from tomeris_backup_v017 import'); p.write_text(s,encoding='utf-8')
