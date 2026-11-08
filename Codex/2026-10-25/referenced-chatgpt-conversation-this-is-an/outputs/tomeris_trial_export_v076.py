"""Export explicitly selected reviewed trials; never choose a review or split silently."""
import argparse,json,re
from pathlib import Path
from tomeris_research_trials import digest,key
from tomeris_bandit_lab import ACTIONS,validate

def read(path):
    with Path(path).open('rb') as f:raw=f.read(1000001)
    if len(raw)>1000000:raise ValueError('入力ファイルは1MB以内です。')
    return json.loads(raw)

def child(root,name):
    if not isinstance(name,str) or not name or '/' in name or '\\' in name or ':' in name:raise ValueError('入力は記録フォルダー内のファイル名で指定してください。')
    path=(root/name).resolve()
    if path.parent!=root or path.suffix!='.json':raise ValueError('記録フォルダー外は読みません。')
    return path

def dataset(directory,manifest):
    root=Path(directory).resolve()
    if not isinstance(manifest,list) or not 4<=len(manifest)<=1000:raise ValueError('選択表は4〜1000件必要です。')
    result=[];seen=set();partition={}
    for entry in manifest:
        if not isinstance(entry,dict):raise ValueError('選択表の行が不正です。')
        split=entry.get('split');group=entry.get('topic_id')
        if split not in ('train','test') or not isinstance(group,str) or not group.strip():raise ValueError('対象グループと学習／評価の区分が必要です。')
        envelope=read(child(root,entry.get('record')));review=read(child(root,entry.get('review')))
        if not isinstance(envelope,dict) or not isinstance(review,dict):raise ValueError('記録形式が不正です。')
        record=envelope.get('record')
        if not isinstance(record,dict) or record.get('version')!=1 or review.get('version')!=1:raise ValueError('記録バージョンが不正です。')
        checksum=digest(record);record_id=record.get('id')
        if not isinstance(record_id,str) or not re.fullmatch('[a-f0-9]{32}',record_id):raise ValueError('記録IDが不正です。')
        if record_id in seen:raise ValueError('同じ試行を重複選択できません。訂正評価は一つだけ指定してください。')
        seen.add(record_id)
        if envelope.get('sha256')!=checksum or review.get('record_sha256')!=checksum or review.get('trial_id')!=record_id:raise ValueError('比較記録と評価の対応が一致しません。')
        if review.get('origin')!='human_reviewed' or review.get('production_enabled') is not False:raise ValueError('人が記入した未適用の評価だけを使用できます。')
        ratings=review.get('ratings');reason=review.get('reason')
        if not isinstance(ratings,dict) or set(ratings)!=set(ACTIONS) or any(type(v) is not int or v not in (-1,0,1) for v in ratings.values()):raise ValueError('未採点または不正な点数です。')
        if not isinstance(reason,str) or not 5<=len(reason.strip())<=2000:raise ValueError('採点理由が必要です。')
        tops=[]
        for action in ACTIONS:
            ranking=record.get('rankings',{}).get(action)
            if not isinstance(ranking,list) or not ranking or not isinstance(ranking[0],str):raise ValueError('比較対象がありません。')
            url=ranking[0];tops.append(url)
            page=next((p for p in record.get('pages',[]) if p.get('url')==url),None)
            if not page or page.get('status')!='retrieved' or not isinstance(page.get('page'),dict):raise ValueError('両方の先頭候補の本文取得が必要です。')
            text=page['page'].get('text');quotes=page.get('excerpts')
            if not isinstance(text,str) or not text.strip() or not isinstance(quotes,list) or not quotes or not all(isinstance(q,str) and q and q in text for q in quotes):raise ValueError('本文と引用の一致を確認できません。')
        if tops[0]==tops[1] and len(set(ratings.values()))!=1:raise ValueError('同じ先頭資料に異なる点数が付いています。評価を見直してください。')
        query=record.get('query')
        if not isinstance(query,str) or not query.strip():raise ValueError('検索対象がありません。')
        for token in [('group',key(group)),('query',key(query))]+[('url',u) for u in tops]:
            if token in partition and partition[token]!=split:raise ValueError('同じ対象・検索語・資料が学習と評価に跨っています。')
            partition[token]=split
        result.append(dict(id=record_id,topic_id=key(group),context=record.get('context'),split=split,
                           origin='human_reviewed',reason=reason,rewards=ratings,
                           provenance=dict(record_sha256=checksum,review_file=entry['review'],review_sha256=digest(review),retrieved_at=record.get('finished_at'),urls=tops)))
    validate(result)
    for split in ('train','test'):
        if {r['context'] for r in result if r['split']==split}!={'overview','specific'}:raise ValueError('学習・評価のそれぞれに概要と具体的質問が必要です。')
    return result

def export(directory,manifest,output):
    rows=dataset(directory,manifest)
    with Path(output).open('x',encoding='utf-8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
    return len(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(str(export(args.directory,read(args.manifest),args.output))+'件を書き出しました。学習・通常回答への反映はしていません。')

if __name__=='__main__':main()
