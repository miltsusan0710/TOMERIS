from pathlib import Path
p=Path('outputs/tomeris_desktop.py');s=p.read_text(encoding='utf-8');p.write_text(s.replace('tomeris_desktop_v037','tomeris_desktop_v038'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8');s=s.replace('起動先：tomeris_desktop_v037.py。204件の自動テスト成功、work/check_context_boundaries_ui.py 成功。','起動先：tomeris_desktop_v038.py。210件の自動テスト成功、work/check_v038_ui.py 成功。')
s=s.replace('6. 【次に修正】','6. 【完了 v0.38】')
s+='''

## v0.38 継続実行の結果
URLや画面案内だけの抜粋を除外するtomeris_prose_evidence.pyを追加。URLを除いた部分でも全対象語が一致し、一定長の説明文がある場合だけ、元の文を変更せず表示する。これは文章形式のフィルターで、意味の正しさや事実の検証ではない。説明を取りこぼす可能性もある。
tomeris_evidence_v029.pyにはサービス別抽出関数の任意フックだけを追加。指定のない旧版は従来passagesのまま。旧GUI・旧抽出モジュール・本番データは保持。新GUI v0.38だけが新抽出を指定。
210件の回帰テスト成功（新規6件）。一時データでGUIの会話切替・天気確認も成功。Wikipedia Ollamaの実ページ1件を再取得し、URL・テンプレート行に代わってソフトウェアの説明文2件を原文引用できた。source_learning_live_check_v038.jsonに結果を保存。検索候補が空の部分だけ模擬、ページ取得は実通信。旧実測結果も保存。1件の成功を一般的な正確さ向上とは説明しない。Google/Brave実接続は未検証のまま。
通常起動をv0.38へ更新。予定した項目1〜6は完了。新しい具体的な不具合や依頼がなければ、次回の継続実行で無目的な機能追加・同じ検証の反復をしない。残る一般的な限界は、意味的な裏取り、検索サービスの実接続、自由会話全般の理解であり、実装済みと扱わない。
'''
p.write_text(s,encoding='utf-8')
Path('outputs/README_desktop_v038.md').write_text('''# トメリス v0.38
通常のデスクトップ起動を一度閉じて開き直すと反映されます。

資料の原文抽出からURLだけの行やテンプレート・メニュー案内を除外しました。残る説明文がなければ取得できなかったと報告します。引用をAIで書き直す処理は追加していません。

検証：210件の自動テストと一時データのGUI操作が成功。Wikipedia Ollama記事1件の実取得では、以前のリンク行ではなく説明文を引用しました。文章形式の判定であり、事実の裏取りや全サイトでの適切な抽出を保証するものではありません。

既存の記憶・計画・保存資料は変更していません。過去GUIは保持しています。Google/Braveの有効キーによる実接続は未検証です。
''',encoding='utf-8')
