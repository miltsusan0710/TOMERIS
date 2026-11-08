from pathlib import Path
s=Path('outputs/tomeris_evidence_report.py').read_text(encoding='utf-8-sig')
s=s.replace('from tomeris_grounded_summary import summarize','from tomeris_strict_evidence import terms,passages,relevance_score')
a=s.index('\ndef terms(text):');b=s.index('\ndef needs_clarification',a);s=s[:a]+s[b:]
s=s.replace("len(terms(row.get('title','')+' '+row.get('snippet',''))&wanted)","relevance_score(row.get('title','')+' '+row.get('snippet',''),wanted)")
a=s.index('            summary=None');b=s.index('            if len(domains)<2:',a)
s=s[:a]+'''            answer+='\\n\\n【確認の範囲】\\n自動要約は停止しています。対象語の一致と原文の取得を確認しただけで、記述の正確さ・最新性・公式性・質問への十分性を保証するものではありません。'
'''+s[b:]
s=s.replace('【本文で確認した記述・原文】','【対象語が含まれる本文・原文】')
s=s.replace('ページから関連する記述を抽出しました。','ページから対象語が含まれる記述を抽出しました。')
s=s.replace("        wanted=terms(topic)","        wanted=terms(topic)\n        if not wanted:return self.track(question,'調査対象の名前を特定できませんでした。URLだけでなく「Ollamaの機能」のように対象名も入力してください。')")
# Validate before making requests, not after searching.
check="        wanted=terms(topic)\n        if not wanted:return self.track(question,'調査対象の名前を特定できませんでした。URLだけでなく「Ollamaの機能」のように対象名も入力してください。')\n"
s=s.replace(check,'');s=s.replace('        rows=[];seen=set();failures=[]',check+'        rows=[];seen=set();failures=[]')
Path('outputs/tomeris_evidence_report_v0261.py').write_text(s,encoding='utf-8')
s=Path('outputs/tomeris_desktop_v026.py').read_text(encoding='utf-8-sig').replace('v0.26','v0.26.1').replace('from tomeris_evidence_report import DesktopService as PlanService','from tomeris_evidence_report_v0261 import DesktopService as PlanService')
Path('outputs/tomeris_desktop_v0261.py').write_text(s,encoding='utf-8')
