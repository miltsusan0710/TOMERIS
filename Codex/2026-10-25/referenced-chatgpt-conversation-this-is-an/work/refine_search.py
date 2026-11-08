from pathlib import Path
p=Path('outputs/tomeris_web_search.py');s=p.read_text(encoding='utf-8-sig')
point='class DesktopService(MemoryService):'
addition='''def relevant_results(question, rows):
    # Conservative topic checks; these do not prove accuracy or freshness.
    latin=re.findall(r'[a-zA-Z][a-zA-Z0-9.+-]{2,}',question.lower())
    weather=bool(re.search('天気|天候|予報',question))
    retained=[]
    for row in rows:
        evidence=(row['title']+' '+row['snippet']).lower()
        if latin and not any(term in evidence for term in latin): continue
        if weather and not re.search('天気|天候|予報|気温|降水|weather|forecast',evidence): continue
        retained.append(row)
    return retained

'''
s=s.replace(point,addition+point)
s=s.replace('try: rows=search_web(question)','try: rows=relevant_results(question,search_web(question))')
s=s.replace('検索結果を取得できませんでした。地域名や具体的な語を加えて、もう一度お試しください。最新情報を確認できていません。','質問に使える検索結果を確認できませんでした。検索語を短く具体的にして、もう一度お試しください。最新情報は確認できていません。')
p.write_text(s,encoding='utf-8')
