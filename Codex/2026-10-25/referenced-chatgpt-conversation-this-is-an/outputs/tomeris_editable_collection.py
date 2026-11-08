"""Editable, explicitly saved public topics with a per-session attempt budget."""
import time
from copy import deepcopy
from tomeris_research_boundaries import DesktopService as BaseService
from tomeris_topic_settings import TopicSettings,validate_topics
from tomeris_search_methods import wikipedia_search,wikipedia_page,MethodError
from tomeris_prose_evidence import passages
class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.topic_store=TopicSettings(self.data_dir);self.topic_error='';self.topic_results=[];self.topic_cursor=0
        try:self.collection_topics=self.topic_store.load()
        except (ValueError,OSError,UnicodeError):
            self.collection_topics=[];self.topic_error='テーマを読み取れないため収集を停止しています。';self.auto_sources_enabled=False
    def set_auto_collection(self,enabled):
        if enabled and self.topic_error:raise ValueError(self.topic_error)
        return super().set_auto_collection(enabled)
    def collection_state(self):
        return dict(topics=list(self.collection_topics),enabled=self.auto_sources_enabled,attempts=self.auto_sources_index,results=deepcopy(self.topic_results),error=self.topic_error or self.auto_settings_error)
    def save_collection_topics(self,topics):
        validate_topics(dict(version=1,topics=topics))
        if self.topic_error:raise ValueError(self.topic_error)
        self.set_auto_collection(False) # Persist stop first; a failed topic write stays stopped.
        self.topic_store.save(topics)
        self.collection_topics=list(topics);self.topic_cursor=0
        self.auto_sources_next=time.monotonic()+600
        return 'テーマを保存し、自動収集を停止しました。内容を確認して「再開」を押してください。今回の試行上限はリセットしません。'
    def auto_sources_due(self):
        return bool(self.collection_topics) and not self.topic_error and super().auto_sources_due() and self.topic_cursor<len(self.collection_topics)
    def collect_public_topic(self):
        if not self.auto_sources_due():return None
        topic=self.collection_topics[self.topic_cursor];self.topic_cursor+=1;self.auto_sources_index+=1;self.auto_sources_next=time.monotonic()+600
        status='取得失敗';url=''
        try:
            row=next((r for r in wikipedia_search(topic) if r.get('title')==topic),None)
            if not row:raise MethodError('同名の記事を確認できませんでした。')
            page=wikipedia_page(row);quotes=passages(page,topic)
            if not quotes:raise MethodError('説明文を抽出できませんでした。')
            count=self.catalogue.learn([dict(page=page,excerpts=quotes)])
            status=f'未検証資料 {count}件保存';url=page['url']
        except (ValueError,OSError) as exc:status='取得失敗：'+str(exc)
        self.topic_results.append(dict(topic=topic,status=status,url=url))
        self.auto_sources_status=topic+'：'+status
        return self.auto_sources_status+'。能力向上を確認したという意味ではありません。'
    def prepare_context(self,text):
        q,answer=super().prepare_context(text)
        if text.strip().rstrip('。！？!?') in ('自動資料収集を停止','自動資料収集を再開','自動資料収集の状態') and answer:
            answer=answer.replace('Wikipediaの固定3テーマのみ','Wikipediaの保存済みテーマのみ')
            answer+='\n対象：'+' ／ '.join(self.collection_topics)
            if self.topic_error:answer+='\n'+self.topic_error
        return q,answer
