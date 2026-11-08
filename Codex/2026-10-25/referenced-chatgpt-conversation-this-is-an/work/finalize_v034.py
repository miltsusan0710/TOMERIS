from pathlib import Path
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('起動先：tomeris_desktop_v033.py。175件の自動テスト成功、work/check_v033_ui.py 成功。','起動先：tomeris_desktop_v034.py。181件の自動テスト成功、work/check_source_backup_ui.py 成功。')
s=s.replace('1. 新しいresearch_sources.jsonをバックアップ・別フォルダー復元に安全に含める。古いZIPとの互換性を保ち、破損形式・容量・URLを検証し、ユーザー本番データでテストしない。Google報告HTMLは別扱いのまま。','1. 【完了 v0.34】research_sources.jsonのバックアップ・別フォルダー復元。古いZIPも読める。新規tomeris_backup_v034.py/tomeris_restore_v034.pyと独立したtomeris_catalogue_schema.pyで形式・容量・URL・日時を検証。最新GUIのDesktopServiceで該当メソッドを上書きしている。Google報告HTMLは対象外のまま。')
s+='\n## 2026-10-29 継続実行の結果\n資料のバックアップ対応を完了。既存バックアップ／復元モジュールと旧GUIは変更せず新規版を追加。次は項目2の資料管理画面。v0.34のバックアップが実際に呼ばれるよう最新GUIのDesktopServiceにメソッド割り当てがある点に注意。復元時の資料検証は厳密だが、現状のCatalogue通常読み込みはより緩い。次の資料管理改善時に共通検証の採用を検討し、不正ファイルを黙って上書きしないこと。\n'
p.write_text(s,encoding='utf-8')
Path('outputs/tomeris_desktop.py').write_text('"""Stable entry point for the desktop shortcut."""\nfrom tomeris_desktop_v034 import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
