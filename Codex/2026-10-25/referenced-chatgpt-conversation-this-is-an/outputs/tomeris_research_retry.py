"""Explicit, expiring research retry review. Never replay stored answers."""
import re,secrets,time
from tomeris_research_history_v044 import DesktopService as BaseService
from tomeris_auto_research_v029 import instruction
MODES={'自動','Wikipedia（日本語）','Wikipedia（英語）','Wikipedia（日英）','Brave API','併用（Wikipedia＋Brave）','Bing RSS（試験）'}
class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.retry_review=None
    def clear_tool_context(self):
        super().clear_tool_context();self.retry_review=None
    def prepare_context(self,text):
        command=text.strip()
        match=re.fullmatch(r'/research-retry ([0-9a-f]{32})',command)
        if match:
            self.clear_tool_context()
            try:
                row=self.research_journal.get(match[1])
                mode=row['method'].removeprefix('選択設定：').split('（実際の提供元',1)[0]
                if mode not in MODES:raise ValueError('unknown method')
                explicit=instruction(row['question'])[0]
                if explicit and explicit!=mode:raise ValueError('method mismatch')
            except (ValueError,OSError,UnicodeError):return text,self.track(text,'履歴または保存された方法を確認できません。再調査は実行していません。')
            token=secrets.token_hex(16)
            self.retry_review=dict(row=row,mode=mode,token=token,expires=time.monotonic()+300)
            answer='再調査の確認（まだ送信していません）\n質問：'+row['question']+'\n選択方法：'+mode+'\n検索サービスへこの質問を送信し、公開ページを新しく取得します。保存した本文は使いません。\n実行：/research-confirm '+token+'\n取り消し：キャンセル（確認は5分間有効）'
            return text,self.track(text,answer)
        match=re.fullmatch(r'/research-confirm ([0-9a-f]{32})',command)
        if match:
            review=self.retry_review;self.retry_review=None
            if not review or review['token']!=match[1] or time.monotonic()>review['expires']:
                return text,self.track(text,'確認が無効または期限切れです。履歴から再調査の確認を開き直してください。')
            try:
                if self.research_journal.get(review['row']['id'])!=review['row']:raise ValueError('changed')
            except (ValueError,OSError,UnicodeError):return text,self.track(text,'確認後に履歴が変わりました。再調査は実行していません。')
            self.clear_tool_context()
            old=self.methods.mode
            try:
                self.methods.mode=review['mode']
                answer=self.report(review['row']['question'])
            finally:self.methods.mode=old
            return text,'履歴からの再調査（今回の取得結果）\n'+answer
        self.retry_review=None
        return super().prepare_context(text)
