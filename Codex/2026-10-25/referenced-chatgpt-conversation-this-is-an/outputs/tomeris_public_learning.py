"""Bounded public-source collection, not model training or self-modification."""
import time
from tomeris_persona import DesktopService as BaseService
from tomeris_search_methods import wikipedia_search,wikipedia_page,MethodError
from tomeris_prose_evidence import passages
TOPICS=('論理的思考','認知バイアス','情報リテラシー')
class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.auto_sources_enabled=True;self.auto_sources_next=time.monotonic()+600;self.auto_sources_index=0;self.auto_sources_status='開始待ち'
    def auto_sources_due(self):
        return self.auto_sources_enabled and self.catalogue.enabled and not self.demo and self.auto_sources_index<len(TOPICS) and time.monotonic()>=self.auto_sources_next
    def collect_public_topic(self):
        if not self.auto_sources_due():return None
        topic=TOPICS[self.auto_sources_index];self.auto_sources_index+=1;self.auto_sources_next=time.monotonic()+600
        try:
            rows=wikipedia_search(topic)
            # One exact-title article per tick; no autonomous link traversal.
            row=next((r for r in rows if r.get('title')==topic),None)
            if not row:raise MethodError('同名の記事を確認できませんでした。')
            page=wikipedia_page(row);quotes=passages(page,topic)
            if not quotes:raise MethodError('対象の説明文を抽出できませんでした。')
            count=self.catalogue.learn([dict(page=page,excerpts=quotes)])
            self.auto_sources_status=f'「{topic}」：未検証資料を{count}件保存。'
        except (ValueError,OSError) as exc:self.auto_sources_status=f'「{topic}」：保存できませんでした。'+str(exc)
        return self.auto_sources_status+' モデルの学習・能力向上を確認したという意味ではありません。'
    def prepare_context(self,text):
        command=text.strip().rstrip('。！？!?')
        if command in ('自動資料収集を停止','自動資料収集を再開','自動資料収集の状態'):
            self.clear_tool_context()
            if command=='自動資料収集を停止':self.auto_sources_enabled=False
            elif command=='自動資料収集を再開':self.auto_sources_enabled=True
            answer=('自動資料収集：有効' if self.auto_sources_enabled else '自動資料収集：停止中')+f'\n今回の起動で {self.auto_sources_index}/{len(TOPICS)} テーマを試行。'+self.auto_sources_status
            answer+='\n公開Wikipediaの一般知識のみ。個人の会話・予定は検索に送りません。アプリ起動中、10分以上の間隔で最大3テーマです。設定はこの起動中のみ。資料学習を停止中は収集しません。'
            return text,self.track(text,answer)
        return super().prepare_context(text)
