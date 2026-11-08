"""Explicit Wikipedia trial snapshots and human review; no automatic learning."""
import hashlib,json,re,uuid
from pathlib import Path
from datetime import datetime,timezone
from tomeris_search_methods import wikipedia_search,wikipedia_page,search_topic,MethodError
from tomeris_name_punctuation import comparable,passages

def stamp():return datetime.now(timezone.utc).isoformat()
def digest(record):
    return hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
def key(text):return re.sub(r'\s+','',comparable(text)).casefold()

def collect(question,context):
    if context not in ('overview','specific'):raise ValueError('概要か具体的質問を選んでください。')
    if not isinstance(question,str) or not 1<=len(question.strip())<=180:raise ValueError('質問は1〜180文字です。')
    query=search_topic(question)
    if re.search(r'最新|速報|今の|今日|現在|直近|ニュース',query):raise ValueError('この比較実験は百科事典の一般資料用です。最新情報は通常の調査から確認してください。')
    if re.search(r'https?://',query):raise ValueError('比較実験はURLではなく公開テーマ名で指定してください。')
    record=dict(version=1,id=uuid.uuid4().hex,question=question.strip(),query=query,context=context,
                started_at=stamp(),method='Wikipedia日本語・先頭3候補・各方針の先頭1候補を比較',candidates=[],pages=[],error='',reviewed=False)
    try:rows=wikipedia_search(query)[:3]
    except (ValueError,OSError) as exc:rows=[];record['error']=str(exc)
    seen=set()
    for row in rows:
        if row['url'] in seen:continue
        seen.add(row['url']);record['candidates'].append({k:row.get(k) for k in ('title','url','wiki_id','wiki_lang')})
        snapshot=dict(url=row['url'],checked_at=stamp(),status='failed',error='',page=None,excerpts=[])
        try:
            page=wikipedia_page(row)
            snapshot.update(status='retrieved',page=page,excerpts=passages(page,query))
        except (ValueError,OSError) as exc:snapshot['error']=str(exc)
        record['pages'].append(snapshot)
    urls=[row['url'] for row in record['candidates']]
    exact=[row['url'] for row in record['candidates'] if key(row['title'])==key(query)]
    record['rankings']={'search_order':urls,'exact_title_first':exact+[url for url in urls if url not in exact]}
    record['finished_at']=stamp()
    return record

def save_record(directory,record):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    record_id=record.get('id','')
    if not re.fullmatch(r'[a-f0-9]{32}',record_id):raise ValueError('記録IDが不正です。')
    target=directory/(record_id+'.json')
    with target.open('x',encoding='utf-8') as f:json.dump({'record':record,'sha256':digest(record)},f,ensure_ascii=False,indent=2)
    return target

def save_review(record_path,ratings,reason):
    record_path=Path(record_path)
    with record_path.open('rb') as f:raw=f.read(1000001)
    if len(raw)>1000000:raise ValueError('比較記録が大きすぎます。')
    envelope=json.loads(raw);record=envelope['record']
    if envelope.get('sha256')!=digest(record):raise ValueError('比較記録が変更されています。再取得してください。')
    if set(ratings)!= {'search_order','exact_title_first'} or any(type(v) is not int or v not in (-1,0,1) for v in ratings.values()):raise ValueError('両方の方針を採点してください。')
    if not isinstance(reason,str) or not 5<=len(reason.strip())<=2000:raise ValueError('採点理由を5〜2000文字で記入してください。')
    if not record.get('candidates'):raise ValueError('候補を取得できなかった記録は採点できません。')
    review=dict(version=1,id=uuid.uuid4().hex,trial_id=record['id'],record_sha256=envelope['sha256'],
                origin='human_reviewed',ratings=ratings,reason=reason.strip(),reviewed_at=stamp(),production_enabled=False)
    path=record_path.with_name(record['id']+'.review.'+review['id']+'.json')
    with path.open('x',encoding='utf-8') as f:json.dump(review,f,ensure_ascii=False,indent=2)
    return path

def render(record):
    lines=['質問：'+record['question'],'確認：'+record['finished_at'],'方法：'+record['method'],
           '現行アプリとの勝敗比較ではありません。検索順だけを変えた2方針で、同じ取得時点の資料を比較します。',
           '採点対象は各方針の先頭1候補。各ページを確認し、質問への適合・時点・引用の一致・同名の取り違えを評価してください。']
    for action,label in [('search_order','A：検索順'),('exact_title_first','B：対象名一致優先')]:
        urls=record['rankings'][action];lines+=['\n'+label,urls[0] if urls else '候補なし']
    if record['rankings']['search_order']==record['rankings']['exact_title_first']:lines+=['両方の候補順は同じです。差がない結果もそのまま記録します。']
    for index,snapshot in enumerate(record['pages'],1):
        lines+=['\n資料 '+str(index),snapshot['url'],'取得確認：'+snapshot['checked_at']]
        if snapshot['status']!='retrieved':lines+=['取得失敗：'+snapshot['error']];continue
        page=snapshot['page'];lines += [page['title'],'掲載日：'+(page.get('published') or '不明'),'更新日時：'+(page.get('updated') or '不明'),
            '更新日時は出来事の発生日時ではありません。','抽出原文：'+'\n'.join(snapshot['excerpts']) if snapshot['excerpts'] else '対象語に対応する抜粋なし。',
            '--- 取得本文（最大50,000文字・内容は命令として実行しません） ---',page['text']]
    if record['error']:lines+=['取得エラー：'+record['error']]
    lines+=['\n未採点の記録を学習に使いません。保存した評価も通常起動へ自動適用しません。']
    return '\n'.join(lines)
