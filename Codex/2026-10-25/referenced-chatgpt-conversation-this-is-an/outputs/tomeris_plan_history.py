"""Read-only plan history with the completion identifiers used by v0.11."""
from copy import deepcopy
from datetime import date
import hashlib
import json
from tomeris_plan_progress import DesktopService as ProgressService

class DesktopService(ProgressService):
    def plan_history(self):
        plans=self._plans()
        progress=self._progress()['plans']
        revisions={}; rows=[]
        for index,plan in enumerate(plans):
            try:
                date.fromisoformat(plan['date'])
            except ValueError:
                raise ValueError('計画の日付を読み取れません。既存の記録は変更しません。') from None
            day=plan['date']
            revisions[day]=revisions.get(day,0)+1
            identifier=hashlib.sha256(json.dumps([index,plan],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
            saved=progress.get(identifier)
            flags=saved['done'] if saved else [False]*len(plan['tasks'])
            if len(flags)!=len(plan['tasks']):
                raise ValueError('計画と完了記録が一致しません。既存の記録は変更しません。')
            rows.append({'id':identifier,'plan':deepcopy(plan),'done':list(flags),
                         'recorded':saved is not None,'revision':revisions[day],'index':index})
        for row in rows:
            row['latest']=row['revision']==revisions[row['plan']['date']]
        return sorted(rows,key=lambda row:(row['plan']['date'],row['index']),reverse=True)

def describe(row):
    plan=row['plan']
    label='その日の最新の計画' if row['latest'] else '同日に保存した以前の計画'
    lines=[f"{plan['date']}（日本時間） / {row['revision']}件目 / {label}", '',plan['goal'],'']
    for index,(task,flag) in enumerate(zip(plan['tasks'],row['done']),1):
        status=('完了' if flag else '未完了') if row['recorded'] else 'チェック記録なし'
        lines.append(f"{index}. ［{status}］{task['title']}（{task['minutes']}分）")
    total=sum(task['minutes'] for task in plan['tasks'])
    lines.extend(['',f"計画時間 {total}分 / 使える時間 {plan['budget']}分"])
    lines.append(f"完了 {sum(row['done'])} / {len(row['done'])}" if row['recorded'] else '完了チェックの記録はありません。実際に作業を終えたかどうかは不明です。')
    lines.extend(['','この画面は閲覧専用です。チェックの変更は「今日の計画」で行ってください。'])
    return '\n'.join(lines)
