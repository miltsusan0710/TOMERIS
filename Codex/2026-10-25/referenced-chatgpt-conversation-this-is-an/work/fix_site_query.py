from pathlib import Path
p=Path('outputs/tomeris_site_search.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('def site_query(text):','def site_query(text):\n    if re.match(r"^(その|この|それ|関連|公式|参考)(?:サイト|URL|リンク)",text,re.I): return None')
s=s.replace("    topic=re.sub(r'(?:に関する|についての|の)$','',topic).strip()","    topic=re.sub(r'(?:公式|関連|参考)$','',topic).strip()\n    topic=re.sub(r'(?:に関する|についての|の)$','',topic).strip()")
p.write_text(s,encoding='utf-8')
