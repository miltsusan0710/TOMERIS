"""At most two concurrent reads; catalogue writes stay on the service worker."""
import time
from concurrent.futures import ThreadPoolExecutor
from tomeris_editable_collection import DesktopService as BaseService
from tomeris_search_methods import wikipedia_search,wikipedia_page,MethodError
from tomeris_prose_evidence import passages

def fetch_topic(topic):
    row=next((r for r in wikipedia_search(topic) if r.get('title')==topic),None)
    if not row:raise MethodError('同名の記事を確認できませんでした。')
    page=wikipedia_page(row);quotes=passages(page,topic)
    if not quotes:raise MethodError('説明文を抽出できませんでした。')
    return dict(page=page,excerpts=quotes)

class DesktopService(BaseService):
    def collect_public_topic(self):
        if not self.auto_sources_due():return None
        count=min(2,3-self.auto_sources_index,len(self.collection_topics)-self.topic_cursor)
        topics=self.collection_topics[self.topic_cursor:self.topic_cursor+count]
        self.topic_cursor+=count;self.auto_sources_index+=count
        self.auto_sources_next=time.monotonic()+600
        try:
            with ThreadPoolExecutor(max_workers=2,thread_name_prefix='tomeris-source') as pool:
                futures=[pool.submit(fetch_topic,topic) for topic in topics]
                for topic,future in zip(topics,futures):
                    url=''
                    try:
                        item=future.result()
                        saved=self.catalogue.learn([item])
                        status=f'未検証資料 {saved}件保存';url=item['page']['url']
                    except (ValueError,OSError) as exc:status='取得・保存失敗：'+str(exc)
                    except Exception:status='取得処理で予期しないエラーが発生しました。'
                    self.topic_results.append(dict(topic=topic,status=status,url=url))
        finally:self.auto_sources_next=time.monotonic()+600
        self.auto_sources_status=' ／ '.join(r['topic']+'：'+r['status'] for r in self.topic_results[-count:])
        return self.auto_sources_status+'。最大2テーマを同時取得。資料は未検証です。'
    def prepare_context(self,text):
        query,answer=super().prepare_context(text)
        if answer and text.strip().rstrip('。！？!?') in ('自動資料収集を停止','自動資料収集を再開','自動資料収集の状態'):
            answer+='\n同時取得は最大2テーマ、1起動で合計3試行まで。次の取得は前回完了から10分以上空けます。'
        return query,answer
