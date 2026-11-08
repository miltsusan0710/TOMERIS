"""Read-only accounting of retrieval failures, independent of reward datasets."""
import argparse,json,re
from pathlib import Path
from datetime import datetime,timezone
from tomeris_trial_export import child,read
from tomeris_research_trials import digest

def classify(record):
    candidates=record['candidates'];pages=record['pages'];rankings=record['rankings']
    if not isinstance(candidates,list) or not isinstance(pages,list) or not isinstance(rankings,dict):raise ValueError('不正な記録形式')
    if not candidates:return 'search_error' if record.get('error') else 'no_candidates'
    evidence=[]
    for action in ('search_order','exact_title_first'):
        ranking=rankings.get(action)
        if not isinstance(ranking,list) or not ranking or not isinstance(ranking[0],str):raise ValueError('順位が不正')
        matches=[p for p in pages if isinstance(p,dict) and p.get('url')==ranking[0]]
        if len(matches)!=1:raise ValueError('先頭資料の記録が欠落または重複')
        snapshot=matches[0];page=snapshot.get('page')
        if snapshot.get('status')=='failed':evidence.append('failed');continue
        if snapshot.get('status')!='retrieved' or not isinstance(page,dict):raise ValueError('取得状態が不正')
        text=page.get('text');quotes=snapshot.get('excerpts')
        evidence.append('evidence' if isinstance(text,str) and text.strip() and isinstance(quotes,list) and quotes and all(isinstance(q,str) and q and q in text for q in quotes) else 'no_evidence')
    if 'failed' in evidence:return 'retrieval_failed'
    if 'no_evidence' in evidence:return 'no_matching_evidence'
    return 'both_have_evidence'

def summarize(directory):
    root=Path(directory).resolve()
    counts={k:0 for k in ('search_error','no_candidates','retrieval_failed','no_matching_evidence','both_have_evidence','invalid')}
    records=[]
    if root.exists():
        for path in root.glob('*.json'):
            if '.review.' in path.name:continue
            if len(records)>=10000:raise ValueError('記録が10000件を超えています。集計を中止しました。')
            item={'file':path.name}
            try:
                if not re.fullmatch('[a-f0-9]{32}\\.json',path.name):raise ValueError('記録ファイル名が不正')
                envelope=read(child(root,path.name));record=envelope['record']
                if record['version']!=1 or record['id']!=path.stem or envelope['sha256']!=digest(record):raise ValueError('記録の対応が不一致')
                finished=record['finished_at'];parsed=datetime.fromisoformat(finished)
                if parsed.utcoffset() is None:raise ValueError('取得日時のタイムゾーンがありません')
                item.update(status=classify(record),finished_at=finished,sha256=envelope['sha256'])
            except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:item.update(status='invalid',error=str(exc))
            counts[item['status']]+=1;records.append(item)
    return dict(version=1,created_at=datetime.now(timezone.utc).isoformat(),total=len(records),counts=counts,records=records,
                limitation='保存済み比較試行だけの取得状況です。未保存試行は含まず、正答率・採点済み件数・現行アプリの性能ではありません。本文と引用の一致は意味の正しさを保証しません。',production_enabled=False)

def main():
    parser=argparse.ArgumentParser(description='失敗を含む比較試行の読み取り専用集計')
    parser.add_argument('directory',type=Path);args=parser.parse_args()
    print(json.dumps(summarize(args.directory),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
