"""Learn bounded retrieval-order preferences from observable evidence availability."""
import json,os,tempfile,time
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from tomeris_distinct_evidence import DesktopService as BaseService
from tomeris_search_methods import wikipedia_search,wikipedia_page,MethodError
from tomeris_name_punctuation import comparable,passages

ACTIONS=('exact','normalized')

def order(history):
    def rate(action):
        rows=[r for r in history if r['action']==action]
        return (sum(r['success'] for r in rows)+1)/(len(rows)+2)
    return sorted(ACTIONS,key=lambda action:-rate(action))

def fetch(topic,actions,*,search=None,page_reader=None):
    search=search or wikipedia_search;page_reader=page_reader or wikipedia_page
    rows=search(topic)[:5];attempts=[];cache={}
    for action in actions:
        row=next((r for r in rows if (r.get('title')==topic if action=='exact' else comparable(r.get('title',''))==comparable(topic))),None)
        item=None
        if row:
            url=row['url']
            if url not in cache:
                try:
                    page=page_reader(row);quotes=passages(page,topic)
                    cache[url]=dict(page=page,excerpts=quotes) if quotes and all(q in page['text'] for q in quotes) else None
                except (ValueError,OSError):cache[url]=None
            item=cache[url]
        attempts.append(dict(action=action,success=item is not None))
        if item:return item,attempts
    return None,attempts

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.adaptive_path=self.data_dir/'retrieval_experience.json';self.adaptive_history=[];self.adaptive_error=''
        try:
            if self.adaptive_path.exists():
                with self.adaptive_path.open('rb') as f:raw=f.read(200001)
                if len(raw)>200000:raise ValueError('容量超過')
                data=json.loads(raw);rows=data['attempts']
                if data.get('version')!=1 or not isinstance(rows,list) or len(rows)>500:raise ValueError('形式不正')
                for row in rows:
                    if not isinstance(row,dict) or row.get('action') not in ACTIONS or type(row.get('success')) is not bool:raise ValueError('形式不正')
                self.adaptive_history=rows
        except (OSError,ValueError,KeyError,TypeError):
            self.adaptive_error='取得経験を読めないため、経験による順序変更を停止しています。'

    def remember_attempts(self,attempts):
        if self.adaptive_error:return
        stamp=datetime.now(timezone.utc).isoformat()
        rows=(self.adaptive_history+[dict(r,recorded_at=stamp) for r in attempts])[-500:]
        fd,path=tempfile.mkstemp(prefix='retrieval_experience_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                json.dump(dict(version=1,attempts=rows),f);f.flush();os.fsync(f.fileno())
            os.replace(path,self.adaptive_path);self.adaptive_history=rows
        finally:
            if os.path.exists(path):os.unlink(path)

    def collect_public_topic(self):
        if not self.auto_sources_due():return None
        topics=self.eligible_topics()[:min(2,12-self.auto_sources_index)]
        try:self.reserve_topics(topics)
        except OSError:
            self.auto_sources_enabled=False
            return '巡回記録を保存できないため自動収集を停止しました。'
        self.auto_sources_index+=len(topics)
        # Every fifth batch probes the original order; failed choices always get a fallback.
        actions=list(ACTIONS) if self.adaptive_error or self.auto_sources_index%10==0 else order(self.adaptive_history)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(fetch,topic,actions) for topic in topics]
                for topic,future in zip(topics,futures):
                    url=''
                    try:
                        item,attempts=future.result()
                        # Evidence availability is observed before storage, not a truth score.
                        try:self.remember_attempts(attempts)
                        except OSError:self.adaptive_error='取得経験を保存できないため、経験による順序変更を停止しています。'
                        if item:
                            count=self.catalogue.learn([item]);url=item['page']['url'];status=f'未検証資料 {count}件保存'
                        else:status='本文・引用を取得できませんでした。'
                    except (ValueError,OSError):status='検索・保存に失敗しました。'
                    except Exception:status='取得処理で予期しないエラーが発生しました。'
                    self.topic_results.append(dict(topic=topic,status=status,url=url))
        finally:self.auto_sources_next=time.monotonic()+600
        self.auto_sources_status=' ／ '.join(r['topic']+'：'+r['status'] for r in self.topic_results[-len(topics):])
        return self.auto_sources_status+'。取得経験で探す順序を調整しますが、内容の正しさや会話能力は学習していません。'

    def collection_state(self):
        result=super().collection_state()
        result['error']=(result['error']+' '+self.adaptive_error).strip()
        result['adaptive_attempts']=len(self.adaptive_history)
        result['adaptive_order']=order(self.adaptive_history) if not self.adaptive_error else list(ACTIONS)
        return result
