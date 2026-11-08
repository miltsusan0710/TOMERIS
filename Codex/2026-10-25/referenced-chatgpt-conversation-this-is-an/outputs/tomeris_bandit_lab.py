"""Offline, full-feedback contextual-bandit experiment, explicitly invoked by the app.

Two retrieval policies, explicit rewards, disjoint topics for train/evaluation.
Not LLM fine-tuning. Unobserved actions cannot be filled with invented rewards.
"""
import argparse,json,math,random
from pathlib import Path

ACTIONS=('search_order','exact_title_first')
CONTEXTS=('overview','specific')

def validate(rows):
    if not isinstance(rows,list) or not 4<=len(rows)<=10000:raise ValueError('評価データは4〜10000行です。')
    ids=set();topics={'train':set(),'test':set()}
    for row in rows:
        if not isinstance(row,dict):raise ValueError('行の形式が不正です。')
        if not isinstance(row.get('id'),str) or not row['id'] or row['id'] in ids:raise ValueError('IDが空または重複しています。')
        ids.add(row['id'])
        if row.get('split') not in topics or row.get('context') not in CONTEXTS:raise ValueError('分割または文脈が不正です。')
        topic=row.get('topic_id')
        if not isinstance(topic,str) or not topic:raise ValueError('評価対象IDが必要です。')
        topics[row['split']].add(topic)
        if row.get('origin') not in ('synthetic','human_reviewed') or not isinstance(row.get('reason'),str) or not row['reason'].strip():raise ValueError('評価者の区分と評価理由が必要です。')
        rewards=row.get('rewards')
        if not isinstance(rewards,dict) or set(rewards)!=set(ACTIONS):raise ValueError('両方の方法を実際に評価した報酬が必要です。未観測を0で埋めないでください。')
        for value in rewards.values():
            if type(value) not in (int,float) or not math.isfinite(value) or not -1<=value<=1:raise ValueError('報酬は-1〜1の有限数です。')
    if not all(topics.values()) or topics['train']&topics['test']:raise ValueError('学習と評価の対象を分離してください。')

def evaluation_details(test,policy):
    cases=[];topics={};contexts={}
    for row in test:
        selected=policy[row['context']];reward=row['rewards'][selected];baseline=row['rewards']['search_order']
        delta=reward-baseline
        cases.append(dict(id=row['id'],topic_id=row['topic_id'],context=row['context'],action=selected,
                          reward=reward,baseline_reward=baseline,delta=delta))
        topics.setdefault(row['topic_id'],[]).append(delta)
        contexts.setdefault(row['context'],[]).append(delta)
    def aggregate(deltas):
        return dict(count=len(deltas),higher=sum(d>0 for d in deltas),equal=sum(d==0 for d in deltas),
                    lower=sum(d<0 for d in deltas),mean_delta=sum(deltas)/len(deltas))
    by_topic={key:aggregate(values) for key,values in topics.items()}
    return dict(cases=cases,by_context={key:aggregate(values) for key,values in contexts.items()},
                by_topic=by_topic,topic_count=len(topics),
                topic_mean_delta=sum(item['mean_delta'] for item in by_topic.values())/len(topics),
                **aggregate([case['delta'] for case in cases]))

def experiment(rows):
    validate(rows)
    # Simulated epsilon-greedy bandit: only the selected action updates its value.
    values={c:{a:0.0 for a in ACTIONS} for c in CONTEXTS}
    counts={c:{a:0 for a in ACTIONS} for c in CONTEXTS}
    train=[r for r in rows if r['split']=='train']
    if set(r['context'] for r in train)!=set(CONTEXTS):raise ValueError('各文脈に学習データが必要です。')
    rng=random.Random(71);log=[]
    for _ in range(20):
        for row in train:
            c=row['context']
            a=rng.choice(ACTIONS) if rng.random()<.2 else max(ACTIONS,key=lambda a:values[c][a])
            reward=row['rewards'][a];counts[c][a]+=1
            values[c][a]+=(reward-values[c][a])/counts[c][a]
            log.append(dict(id=row['id'],action=a,reward=reward))
    policy={c:max(ACTIONS,key=lambda a:values[c][a]) for c in CONTEXTS}
    test=[r for r in rows if r['split']=='test']
    if set(r['context'] for r in test)!=set(CONTEXTS):raise ValueError('各文脈に未使用の評価データが必要です。')
    score=sum(r['rewards'][policy[r['context']]] for r in test)/len(test)
    baseline=sum(r['rewards']['search_order'] for r in test)/len(test)
    return dict(version=1,policy=policy,action_values=values,train_counts=counts,training_log=log,test_count=len(test),
                test_reward=score,baseline_reward=baseline,delta=score-baseline,
                evaluation=evaluation_details(test,policy),
                baseline='実験用search_order固定。現行アプリの性能との比較ではありません。',
                synthetic=any(r['origin']=='synthetic' for r in rows),production_enabled=False,
                limitation='オフラインの全行動報酬付き実験。実検索精度・会話能力の向上を示さず、通常起動へ自動適用しません。')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('dataset',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    with args.dataset.open('rb') as f:raw=f.read(5000001)
    if len(raw)>5000000:raise ValueError('データは5MB以内です。')
    result=experiment(json.loads(raw))
    # Exclusive creation: never replace user datasets or a prior experiment.
    with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
