"""Prepare a reviewed carry-forward draft without changing saved plans."""
from copy import deepcopy
from tomeris_plan_history import DesktopService as HistoryService
from tomeris_plans import validate, today

class DesktopService(HistoryService):
    def carry_draft(self,identifier):
        rows=self.plan_history()
        source=next((row for row in rows if row['id']==identifier),None)
        if source is None:
            raise ValueError('元の計画が見つかりません。「読み直す」で選び直してください。')
        tasks=[deepcopy(task) for task,done in zip(source['plan']['tasks'],source['done']) if not done]
        if not tasks:
            raise ValueError('この計画はすべて完了しています。引き継ぐ行動はありません。')
        draft=validate(source['plan']['goal'],sum(task['minutes'] for task in tasks),tasks)
        note=f"{source['plan']['date']}の{source['revision']}件目から作った下書きです。内容と時間を確認してください。"
        if not source['recorded']:
            note+=' 完了チェックの記録がないため、全行動を入れています。不要な行は消してください。'
        if any(row['plan']['date']==today() for row in rows):
            note+=' 保存すると今日の最新の計画になります。既存の計画は履歴に残ります。'
        draft['notice']=note
        return draft
