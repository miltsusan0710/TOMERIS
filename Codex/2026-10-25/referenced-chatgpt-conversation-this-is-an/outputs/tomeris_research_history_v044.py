"""Persist retrieved-source metadata; explicit chat commands read past records."""
import re
from tomeris_source_followup import DesktopService as BaseService
from tomeris_research_journal import ResearchJournal
from tomeris_auto_research_v029 import instruction

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.research_journal=ResearchJournal(self.data_dir)
    def report(self,question,progress=None,model=None):
        selected=instruction(question)[0] or getattr(self,"pending_method",None) or self.methods.mode
        answer=super().report(question,progress,model)
        record=self.research_source_snapshot
        if record:
            try:
                method='選択設定：'+str(selected)+'（実際の提供元は出典を参照）'
                self.research_journal.append(record['question'],method,record['sources'])
            except (ValueError,OSError,UnicodeError):
                answer+='\n調査履歴には保存できませんでした。既存の履歴は変更していません。'
        return answer
    def prepare_context(self,text):
        command=text.strip()
        if command not in ('調査履歴を見せて','/research-history') and not re.fullmatch(r'/research-(?:show|delete) [0-9a-f]{32}',command):
            return super().prepare_context(text)
        self.clear_tool_context()
        try:
            if command in ('調査履歴を見せて','/research-history'):
                rows=self.research_journal.read()
                lines=['過去の調査履歴です。今回は検索・再取得していません。','最新100件まで保存します。外部カレンダー・天気・地震などの専用取得は対象外です。']
                if not rows:lines.append('保存された調査履歴はありません。')
                for row in reversed(rows[-10:]):lines.extend([row['retrieved_at']+' / '+row['question'],row['id']])
                lines.extend(['直近10件を表示。詳細：/research-show ID','個別削除：/research-delete ID（指定した履歴だけを削除）','再調査の確認：/research-retry ID'])
                answer='\n'.join(lines)
            elif command.startswith('/research-show '):
                row=self.research_journal.get(command.split()[1])
                lines=['過去の調査記録（再取得していません）','質問：'+row['question'],'記録時刻：'+row['retrieved_at'],row['method']]
                for i,s in enumerate(row['sources'],1):lines.extend([f"[{i}] {s['title']}",s['url']])
                lines.append('本文や回答は保存していません。現在の内容・正確さは未確認です。再調査する場合は質問を改めて送信してください。')
                answer='\n'.join(lines)
            else:
                self.research_journal.delete(command.split()[1]);answer='指定した調査履歴を削除しました。記憶・計画・保存資料は保持しています。'
        except (ValueError,OSError,UnicodeError):answer='調査履歴を読み書きできませんでした。指定IDとファイルの状態を確認してください。'
        return text,self.track(text,answer)
