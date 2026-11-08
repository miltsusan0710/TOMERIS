"""Read-only dated plan lookup with short, explicitly scoped follow-ups."""
import re
from datetime import date,timedelta
from tomeris_plans import today
from tomeris_schedule_grounding import DesktopService as BaseService
from tomeris_plan_history import describe

DAY=r'(?:今日|本日|明後日|明日|昨日|一昨日|\d{4}-\d{2}-\d{2}|\d{4}年\d{1,2}月\d{1,2}日)'
FULL=re.compile(r'(?:私の)?('+DAY+r')の(?:私の)?(?:予定|計画|スケジュール)(?:は|は何|は何ですか|を教えて|を教えてください|を見せて|を確認して|を表示して)?')
SHORT=re.compile('('+DAY+r')(?:は)?')

def resolve_day(label):
    base=date.fromisoformat(today())
    offsets={'今日':0,'本日':0,'明日':1,'明後日':2,'昨日':-1,'一昨日':-2}
    if label in offsets:return (base+timedelta(days=offsets[label])).isoformat()
    m=re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日',label)
    return (date(*map(int,m.groups())) if m else date.fromisoformat(label)).isoformat()

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.schedule_context=False
    def clear_tool_context(self):
        super().clear_tool_context();self.schedule_context=False
    def prepare_context(self,text):
        compact=re.sub(r'\s+','',text).rstrip('？?。！!')
        match=FULL.fullmatch(compact)
        if not match and self.schedule_context:match=SHORT.fullmatch(compact)
        if not match:
            self.schedule_context=False
            return super().prepare_context(text)
        self.clear_tool_context();self.schedule_context=True
        try:day=resolve_day(match[1])
        except ValueError:
            return text,self.track(text,'その日付は確認できません。「2026年10月30日の予定」のように実在する日付を指定してください。')
        try:
            row=next((r for r in self.plan_history() if r['plan']['date']==day and r['latest']),None)
            answer=('保存済みの計画\n'+describe(row) if row else f'トメリスに保存された{day}の計画はありません。')
            answer+='\nGoogleカレンダーなど、外部の予定は確認していません。'
        except (OSError,ValueError,TypeError,KeyError):
            answer='保存した計画を読み取れませんでした。予定の有無は確認できていません。'
        return text,self.track(text,answer)
