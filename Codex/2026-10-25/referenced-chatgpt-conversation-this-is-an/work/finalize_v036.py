from pathlib import Path
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('起動先：tomeris_desktop_v035.py。187件の自動テスト成功、work/check_sources_ui.py 成功。','起動先：tomeris_desktop_v036.py。195件の自動テスト成功、work/check_quake_followup_ui.py 成功。')
s=s.replace('3. 地震の後続発表をイベントIDで追跡して、震度速報→震源情報→訂正の順序を扱えるようにする。取消・訓練・異なる地震への取り違えを回帰テスト。勝手な定期ポーリングや警報を追加しない。','3. 【完了 v0.36】tomeris_earthquake_followup.pyでEventID追跡。震度速報→震源情報→訂正／取消、別地震の除外、古い発表への逆戻り拒否を回帰テスト。質問時のみ最新6電文まで読む。自動ポーリング・警報なし。')
s+='\n## v0.36 継続実行の結果\n地震の後続発表の追跡を完了。新GUIはtomeris_earthquake_followup.DesktopServiceを使用。資料管理・バックアップは継承して維持。対象のEventID・発表時刻はRAMのみ、別話題で解除。続報不明時は古い震源を再表示しない。195件のテストとUIで確認。外部API実接続は未実施（模擬XML）。次は項目4の文脈保持の横断回帰シナリオと取り違え修正。\n'
p.write_text(s,encoding='utf-8')
Path('outputs/tomeris_desktop.py').write_text('"""Stable entry point for the desktop shortcut."""\nfrom tomeris_desktop_v036 import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
