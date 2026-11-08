from pathlib import Path
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('起動先：tomeris_desktop_v034.py。181件の自動テスト成功、work/check_source_backup_ui.py 成功。','起動先：tomeris_desktop_v035.py。187件の自動テスト成功、work/check_sources_ui.py 成功。')
s=s.replace('2. 資料一覧を会話テキストだけでなく、検索・個別消去・取得日時・再取得状態を確認できる画面にする。未検証ラベルを残す。','2. 【完了 v0.35】資料管理画面：検索・個別消去・取得日時・再取得状態。未検証ラベルを維持。再取得は明示クリックでだけ行い、保存本文を更新しない。成功／失敗状態はRAMのみ。')
s+='\n## v0.35 継続実行の結果\n資料管理を完了。最新GUIはtomeris_source_management.DesktopServiceを使い、v0.34のバックアップ／復元メソッド割り当てを保持。CheckedCatalogueで通常起動・保存にも共通スキーマ検証を適用。不正資料は元ファイル保持・学習停止。パネルはtomeris_sources_ui.py、UIテストはwork/check_sources_ui.py。次は項目3の地震イベントIDと後続発表の追跡。\n'
p.write_text(s,encoding='utf-8')
Path('outputs/tomeris_desktop.py').write_text('"""Stable entry point for the desktop shortcut."""\nfrom tomeris_desktop_v035 import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
