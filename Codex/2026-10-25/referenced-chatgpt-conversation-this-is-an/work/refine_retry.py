from pathlib import Path
p=Path('outputs/tomeris_research_retry.py');s=p.read_text(encoding='utf-8').replace("if mode not in MODES:raise ValueError('unknown method')","if mode not in MODES:raise ValueError('unknown method')\n                explicit=instruction(row['question'])[0]\n                if explicit and explicit!=mode:raise ValueError('method mismatch')")
p.write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_research_history_v044.py');s=p.read_text(encoding='utf-8').replace("'個別削除：/research-delete ID（指定した履歴だけを削除）'","'個別削除：/research-delete ID（指定した履歴だけを削除）','再調査の確認：/research-retry ID'")
p.write_text(s,encoding='utf-8')
