"""Answer today's personal schedule from saved plans, never model guesses."""
import re
from tomeris_prose_evidence import DesktopService as BaseService


def today_plan_request(text):
    text=re.sub(r'\s+','',text).rstrip('？?。！!')
    return bool(re.fullmatch(r'(?:私の)?(?:今日|本日)の(?:私の)?(?:予定|計画|スケジュール)(?:は|は何|は何ですか|を教えて|を教えてください|を見せて|を確認して|を表示して)?',text))

class DesktopService(BaseService):
    def prepare_context(self,text):
        if not today_plan_request(text):return super().prepare_context(text)
        self.clear_tool_context()
        try:
            current=self.today_plan()
            if current is None:
                answer='トメリスに保存された今日の計画はまだありません。「計画を作る」から登録できます。'
            else:
                p=current['plan']
                lines=[f"保存済みの今日の計画（{p['date']}）",p['goal']]
                lines.extend(f"{i}. ［{'完了' if done else '未完了'}］{task['title']}（{task['minutes']}分）" for i,(task,done) in enumerate(zip(p['tasks'],current['done']),1))
                answer='\n'.join(lines)
            answer+='\nGoogleカレンダーなど、外部の予定は確認していません。'
        except (OSError,ValueError,TypeError,KeyError):
            answer='保存した計画を読み取れませんでした。予定の有無は確認できていません。「今日の計画」画面でも確認してください。'
        return text,self.track(text,answer)
