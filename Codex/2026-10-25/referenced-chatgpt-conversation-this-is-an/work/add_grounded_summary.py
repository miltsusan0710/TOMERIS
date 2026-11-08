from pathlib import Path
p=Path('outputs/tomeris_evidence_report.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('from tomeris_page_reader import fetch_page,PageError','from tomeris_page_reader import fetch_page,PageError\nfrom tomeris_grounded_summary import summarize')
s=s.replace("return self.report('マーベル アイアンマン JARVIS ジャービス',progress)","return self.report('マーベル アイアンマン JARVIS ジャービス',progress,model)")
s=s.replace('return self.report(question,progress)','return self.report(question,progress,model)',2)
# sites has no model parameter; retain extraction-only use there.
s=s.replace('def report(self,question,progress=None):','def report(self,question,progress=None,model=None):')
s=s.replace("            answer+='\\n\\n【未確認の点】\\n原文の抽出であり、AIによる要約は生成していません。情報の正確さ・最新性・公式性を自動認定していません。'", "            summary=None\n            if model in self.model_names:\n                if progress:progress('根拠原文付きで日本語の報告を整理しています…')\n                summary=summarize(question,checked,model)\n            if summary:\n                answer=header+'\\n\\n【資料に基づく整理・AI作成】\\n'+summary+'\\n\\n'+answer[len(header)+2:]\n            answer+='\\n\\n【未確認の点】\\n情報の正確さ・最新性・公式性を自動認定していません。'\n            if summary:answer+='引用の一致と出典番号は検査していますが、要約の意味が正しいかは原文と照らして確認してください。'\n            else:answer+='要約を検証できない、またはモデルが未確認のため、根拠原文だけを表示しています。'")
p.write_text(s,encoding='utf-8')
