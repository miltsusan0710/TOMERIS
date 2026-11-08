from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8').replace('tomeris_desktop_v041','tomeris_desktop_v042'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v041.py。229件の自動テスト成功、work/check_v041_ui.py 成功。','起動先：tomeris_desktop_v042.py。235件の自動テスト成功。v0.42は画面変更なし・GUI起動なしでサービスを検証。')
s=s.replace('10. 【未完了】','10. 【一部完了 v0.42：出典の追加質問】')
s+='''

## v0.42 継続実行結果
優先順位の「自然な会話の文脈保持」に従い項目10を小分けし、「その出典は？」「情報源を教えて」を先行実装。tomeris_source_followup.pyとGUI v042を追加。直前の一般資料調査で実際に本文と引用を取得したページだけをRAMに保持し、出典質問には調査対象・取得時刻・URLを決定的に返す。再取得していないことを明記。検索結果だけ・取得失敗・別話題・取消の後は古い出典を出さず、未確認と返す。モデルを使って出典を生成しない。
通常会話と自動検索の両入口、実際のreport経路、出典の再質問、失敗後の旧出典除去を一時データ・模擬公開ページで6件追加。計235件成功。画面のレイアウト変更なし、今回はアプリ画面の起動なし。既存の記憶・計画・過去版を保持して通常起動v0.42へ反映。実通信の追加検証なし。Google/Braveキー実接続未検証。
対象は一般資料の本文抽出経路のみ。天気・地震・Google専用結果の出典追加質問は未対応で、根拠がない場合は未確認と回答する。次は項目9の調査履歴（保存と検証、UIの閲覧／明示再取得を必要に応じ別回に分割）。項目10の残りは「他の情報は？」「別の話」などの調査範囲明示と横断テスト。今回のRAM保持を永続履歴や自動再調査と説明しない。
''';p.write_text(s,encoding='utf-8')
