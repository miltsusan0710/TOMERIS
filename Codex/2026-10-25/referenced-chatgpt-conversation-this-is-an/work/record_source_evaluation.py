from pathlib import Path
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('5. 資料学習による実効改善を、同じ質問セットで再取得成功率・出典の関連性・重複・応答時間から比較可能にする。モデル自身の自己採点を品質保証に使わない。','5. 【完了：評価基盤】tomeris_evaluate_sources.pyで8条件を学習なし／ありで比較。模擬根拠の取得は2/8→4/8、取得試行は3→6。出典レベルの関連性・重複・所要時間をJSONに記録。モデル採点なし。実Webの正確さ・速さの改善とは断定しない。\n6. 【次に修正】実接続のOllama再取得でURLだけの行や「テンプレートを表示」を根拠として採用する問題を発見。tomeris_strict_evidence.passagesのナビゲーション・URLだけの行の除外と説明文の優先を改善する。work/check_source_reuse_live.pyで同じ公開ページを再確認（少数アクセス）。説明文が取れない場合は未確認とし、見せるためだけに一致条件を緩めない。')
s+='\n## 資料学習評価の実行結果\nアプリ本体の変更なし、起動版はv0.37を維持。8条件×2のオフライン比較ツールが通過。source_learning_evaluation.md/json参照。さらにWikipedia Ollama1件の本文再取得を実通信で確認（検索候補なしだけ模擬）。再取得自体は成功したが出力がURL・テンプレート行に偏ったため、情報の有用性は不合格と判断。source_learning_live_check.jsonとsource_learning_results.mdに記録。次は追加した項目6を修正。具体的な不具合が残っているため継続実行は維持する。\n'
p.write_text(s,encoding='utf-8')
