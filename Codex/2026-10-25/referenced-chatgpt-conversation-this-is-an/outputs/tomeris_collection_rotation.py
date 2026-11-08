"""Rotate bounded public topics across restarts; saved sources are not training."""
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from tomeris_overview import DesktopService as BaseService
from tomeris_parallel_collection import fetch_topic

STANDARD_TOPICS = ('論理的思考','認知バイアス','情報リテラシー','批判的思考','意思決定','問題解決',
                   '統計学','確率','コミュニケーション','時間管理','科学的方法','情報検索')
LIMIT = 12


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotation_path = self.data_dir/'collection_rotation.json'
        self.rotation_recent = {}
        self.rotation_error = ''
        try:
            if self.rotation_path.exists():
                with self.rotation_path.open('rb') as f:
                    raw=f.read(16385)
                if len(raw)>16384:raise ValueError('容量超過')
                data=json.loads(raw)
                if data.get('version')!=1 or not isinstance(data.get('recent'),dict) or len(data['recent'])>50:raise ValueError('形式不正')
                for name, stamp in data['recent'].items():
                    if not isinstance(name,str) or len(name)>80 or not isinstance(stamp,str):raise ValueError('形式不正')
                    parsed=datetime.fromisoformat(stamp)
                    if parsed.tzinfo is None:raise ValueError('時差なし')
                self.rotation_recent=data['recent']
        except (ValueError, OSError, UnicodeError, AttributeError, TypeError):
            self.rotation_error='収集の巡回記録を読めないため自動収集を停止しました。元ファイルは保持しています。'
            self.auto_sources_enabled=False

    def all_collection_topics(self):
        return list(dict.fromkeys(list(self.collection_topics)+list(STANDARD_TOPICS)))

    def eligible_topics(self):
        now=datetime.now(timezone.utc)
        saved={row['title']:row['retrieved'] for row in self.catalogue.rows}
        def elapsed(stamp):
            if not stamp:return float('inf')
            return (now-datetime.fromisoformat(stamp)).total_seconds()
        return sorted([name for name in self.all_collection_topics()
                       if elapsed(self.rotation_recent.get(name))>=86400 and elapsed(saved.get(name))>=7*86400],
                      key=lambda name:self.rotation_recent.get(name,''))

    def set_auto_collection(self, enabled):
        if enabled and getattr(self,'rotation_error',''):raise ValueError(self.rotation_error)
        return super().set_auto_collection(enabled)

    def auto_sources_due(self):
        return (self.auto_sources_enabled and self.catalogue.enabled and not self.demo
                and not self.topic_error and not self.rotation_error and not self.auto_settings_error
                and self.auto_sources_index<LIMIT and time.monotonic()>=self.auto_sources_next
                and bool(self.eligible_topics()))

    def reserve_topics(self, topics):
        recent=dict(self.rotation_recent)
        stamp=datetime.now(timezone.utc).isoformat()
        for name in topics:recent[name]=stamp
        recent=dict(sorted(recent.items(),key=lambda row:row[1])[-50:])
        fd,name=tempfile.mkstemp(prefix='collection_rotation_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                json.dump(dict(version=1,recent=recent),f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
            os.replace(name,self.rotation_path)
        finally:
            if os.path.exists(name):os.unlink(name)
        self.rotation_recent=recent

    def collect_public_topic(self):
        if not self.auto_sources_due():return None
        topics=self.eligible_topics()[:min(2,LIMIT-self.auto_sources_index)]
        try:self.reserve_topics(topics)
        except OSError:
            self.rotation_error='巡回記録を保存できないため停止しました。保存先の空き容量や権限を確認してください。'
            self.auto_sources_enabled=False
            return self.rotation_error
        self.auto_sources_index+=len(topics)
        try:
            with ThreadPoolExecutor(max_workers=2,thread_name_prefix='tomeris-source') as pool:
                futures=[pool.submit(fetch_topic,topic) for topic in topics]
                for topic,future in zip(topics,futures):
                    url=''
                    try:
                        item=future.result();count=self.catalogue.learn([item]);url=item['page']['url']
                        status=f'未検証資料 {count}件保存'
                    except (ValueError,OSError) as exc:status='取得・保存失敗：'+str(exc)
                    except Exception:status='取得処理で予期しないエラーが発生しました。'
                    self.topic_results.append(dict(topic=topic,status=status,url=url))
        finally:self.auto_sources_next=time.monotonic()+600
        self.auto_sources_status=' ／ '.join(r['topic']+'：'+r['status'] for r in self.topic_results[-len(topics):])
        return self.auto_sources_status+'。資料の保存であり、モデルの訓練ではありません。'

    def collection_state(self):
        result=super().collection_state()
        result.update(limit=LIMIT, standard_topics=list(STANDARD_TOPICS), next_topics=self.eligible_topics() if not self.rotation_error else [],
                      error=self.rotation_error or result['error'],results=deepcopy(self.topic_results))
        return result

    def prepare_context(self,text):
        command=text.strip().rstrip('。！？!?')
        if command in ('自動資料収集を停止','自動資料収集を再開','自動資料収集の状態'):
            self.clear_tool_context()
            error=''
            try:
                if command!='自動資料収集の状態':self.set_auto_collection(command=='自動資料収集を再開')
            except (ValueError,OSError) as exc:error=str(exc)
            state=self.collection_state()
            answer=('自動資料収集：有効' if state['enabled'] else '自動資料収集：停止中')+f'\n今回 {state["attempts"]}/{LIMIT} 試行。最大2テーマ並列、完了から10分以上。'
            answer+='\n指定テーマ＋標準12テーマを巡回。保存済み資料は7日、失敗を含む試行は24時間以上空けます。'
            answer+='\n次の対象：'+(' ／ '.join(state['next_topics'][:4]) or '待機中（再取得間隔内）')
            answer+='\nアプリ起動中のみ動作します。'+(error or state['error'])
            return text,self.track(text,answer)
        return super().prepare_context(text)
