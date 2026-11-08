"""Isolated acquisition-order evaluation; never writes application experience."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from tomeris_adaptive_collection import fetch,order,ACTIONS
from tomeris_name_punctuation import comparable
from tomeris_search_methods import wikipedia_search,wikipedia_page

def evaluate(cases,search=wikipedia_search,page_reader=wikipedia_page):
    if not isinstance(cases,list) or not 4<=len(cases)<=12:raise ValueError('課題は4〜12件です。')
    groups={};queries=set()
    for case in cases:
        if not isinstance(case,dict) or case.get('split') not in ('train','test'):raise ValueError('区分が不正です。')
        for field in ('topic','group'):
            if not isinstance(case.get(field),str) or not 1<=len(case[field].strip())<=80:raise ValueError('対象名とグループが必要です。')
        query=comparable(case['topic']).casefold();group=case['group'].strip().casefold()
        if query in queries:raise ValueError('同じ対象を繰り返せません。')
        queries.add(query)
        if group in groups and groups[group]!=case['split']:raise ValueError('同じグループが学習と評価に跨っています。')
        groups[group]=case['split']
    if {c['split'] for c in cases}!={'train','test'}:raise ValueError('学習と評価を分けてください。')
    history=[];records=[];urls={};leakage=False;frozen=None
    for split in ('train','test'):
        if split=='test':frozen=order(history)
        for case in [c for c in cases if c['split']==split]:
            record=dict(**case,checked_at=datetime.now(timezone.utc).isoformat(),pages=[],search_error='')
            try:rows=search(case['topic'])[:5]
            except (OSError,ValueError) as exc:rows=[];record['search_error']=str(exc)
            record['candidates']=rows;cache={}
            for row in rows:
                url=row['url']
                if url in urls and urls[url]!=split:leakage=True
                urls[url]=split
            def reader(row):
                url=row['url']
                if url not in cache:
                    try:
                        page=page_reader(row);cache[url]=page
                        record['pages'].append(dict(url=url,checked_at=datetime.now(timezone.utc).isoformat(),page=page,error=''))
                        actual=page.get('url',url)
                        if actual in urls and urls[actual]!=split:
                            nonlocal_leaks.append(actual)
                        urls[actual]=split
                    except (OSError,ValueError) as exc:
                        cache[url]=None;record['pages'].append(dict(url=url,error=str(exc)))
                if cache[url] is None:raise ValueError('本文取得失敗')
                return cache[url]
            nonlocal_leaks=[]
            actions=order(history) if split=='train' else frozen
            item,attempts=fetch(case['topic'],actions,search=lambda _:rows,page_reader=reader)
            record.update(actions=list(actions),evidence_obtained=item is not None,attempts=attempts)
            if split=='train' and not record['search_error']:history.extend(attempts)
            if split=='test':
                baseline,base_attempts=fetch(case['topic'],ACTIONS,search=lambda _:rows,page_reader=reader)
                record.update(baseline_evidence_obtained=baseline is not None,baseline_attempts=base_attempts)
            leakage=leakage or bool(nonlocal_leaks);records.append(record)
    tests=[r for r in records if r['split']=='test']
    return dict(version=1,policy=frozen,training_attempts=history,records=records,overlap_detected=leakage,
        comparison=None if leakage else dict(count=len(tests),evidence=sum(r['evidence_obtained'] for r in tests),baseline_evidence=sum(r['baseline_evidence_obtained'] for r in tests),
        method_attempts=sum(len(r['attempts']) for r in tests),baseline_method_attempts=sum(len(r['baseline_attempts']) for r in tests)),
        production_enabled=False,limitation='本文・引用の取得可否と方法試行数のみ。正答率・通信回数・会話能力ではありません。同じ取得内容で初期順と経験順を比較し、評価側では経験を更新しません。重複資料があれば比較値を出しません。')

def main():
    p=argparse.ArgumentParser();p.add_argument('cases',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError('既存の評価結果は上書きしません。')
    with a.cases.open('rb') as f:raw=f.read(10001)
    if len(raw)>10000:raise ValueError('課題ファイルは10KB以内です。')
    result=evaluate(json.loads(raw))
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(overlap_detected=result['overlap_detected'],comparison=result['comparison']),ensure_ascii=False))

if __name__=='__main__':main()
