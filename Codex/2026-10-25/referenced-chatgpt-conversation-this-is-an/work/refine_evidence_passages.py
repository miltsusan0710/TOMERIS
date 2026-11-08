from pathlib import Path
p=Path('outputs/tomeris_evidence_report.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("    for line in page['text'].splitlines():", "    lines=page['text'].splitlines()\n    for line_number,line in enumerate(lines):\n        if wanted & terms(line) and line_number+1<len(lines):\n            joined=(line+'\\n'+lines[line_number+1])[:350]\n            if len(joined)>=25:candidates.append((len(terms(joined)&wanted)+1,joined))")
s=s.replace("        if chunk not in chosen:chosen.append(chunk)","        if not any(chunk in existing or existing in chunk for existing in chosen):chosen.append(chunk)")
p.write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_grounded_summary.py');s=p.read_text(encoding='utf-8-sig').replace('最大3点','最大2点').replace('180文字以内の日本語','80文字以内の日本語').replace('完全一致の引用20〜350文字','完全一致の引用20〜200文字')
p.write_text(s,encoding='utf-8')
