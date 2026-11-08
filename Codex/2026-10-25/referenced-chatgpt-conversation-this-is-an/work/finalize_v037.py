from pathlib import Path
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('起動先：tomeris_desktop_v036.py。195件の自動テスト成功、work/check_quake_followup_ui.py 成功。','起動先：tomeris_desktop_v037.py。204件の自動テスト成功、work/check_context_boundaries_ui.py 成功。')
s=s.replace('4. 会話の文脈保持の回帰シナリオを増やす。天気・資料調査・通常会話をまたぐ誤引き継ぎを減らし、対象不明時は確認。既存の「他の情報は？」のソース重複排除を保つ。','4. 【完了 v0.37】tomeris_context_boundaries.pyで明示的な話題変更・取消・検索指定待ち→計算／天気・地域未指定の聞き直し・日付だけ変更・天気／地震の追加質問を整理。9件の横断回帰テスト追加。既存の資料重複排除を維持。自由な会話全体の意味理解を保証するものではない。')
s+='\n## v0.37 継続実行の結果\n文脈の誤引き継ぎ修正を完了。最新GUIはtomeris_context_boundaries.DesktopServiceを使用し、入口の多重呼び出しを_depth相当のガードで避ける（実装名_context_depth）。取消・話題変更は保存データを消さず一時文脈だけをクリア。204件テストと会話画面で確認。次は項目5の資料学習の効果比較。既定の未完了項目が終わったら効果と限界をまとめ、無目的に変更を増やさない。\n'
p.write_text(s,encoding='utf-8')
Path('outputs/tomeris_desktop.py').write_text('"""Stable entry point for the desktop shortcut."""\nfrom tomeris_desktop_v037 import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
