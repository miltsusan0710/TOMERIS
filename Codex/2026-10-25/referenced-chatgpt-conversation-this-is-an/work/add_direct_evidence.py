from pathlib import Path
p=Path('outputs/tomeris_evidence_report.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("if site_request(question) or research_requested(question) or not automatic or needs_search(question):","if site_request(question) or research_requested(question) or re.search(r'https?://',question) or not automatic or needs_search(question):")
s=s.replace('        if needs_clarification(question):',"        direct_urls=re.findall(r'https?://[^\\s<>「」]+',question)[:3]\n        if not direct_urls and needs_clarification(question):")
s=s.replace("        topic=site_query(question) if site_request(question) else research_queries(question)[0]","        topic=question if direct_urls else (site_query(question) if site_request(question) else research_queries(question)[0])")
s=s.replace('        if len(topic)>180:', '        if len(topic)>(3000 if direct_urls else 180):')
s=s.replace("        for query in (topic,topic+' 公式'):","        for url in direct_urls:\n            if public_url(url) and url not in seen:\n                seen.add(url);rows.append(dict(title='指定されたページ',url=url,snippet=topic))\n        for query in (() if direct_urls else (topic,topic+' 公式')):")
p.write_text(s,encoding='utf-8')
