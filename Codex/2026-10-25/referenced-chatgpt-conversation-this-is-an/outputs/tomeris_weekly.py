"""Read-only seven-day report from the latest saved plan of each day."""
from datetime import date,timedelta
from tomeris_plan_reflection import DesktopService as ReflectionService
from tomeris_plans import today

class DesktopService(ReflectionService):
    def weekly_report(self):
        end=date.fromisoformat(today()); start=end-timedelta(days=6)
        rows=[row for row in self.plan_history() if row['latest'] and start<=date.fromisoformat(row['plan']['date'])<=end]
        by_day={row['plan']['date']:row for row in rows}
        report={'start':start.isoformat(),'end':end.isoformat(),'planned_days':len(rows),
                'completed':0,'unchecked':0,'unknown':0,'planned_minutes':0,'reflection_days':0,'days':[]}
        for offset in range(7):
            day=(start+timedelta(days=offset)).isoformat(); row=by_day.get(day)
            report['days'].append({'date':day,'row':row})
            if row is None: continue
            report['planned_minutes']+=sum(task['minutes'] for task in row['plan']['tasks'])
            report['reflection_days']+=bool(row.get('reflection'))
            if row['recorded']:
                report['completed']+=sum(row['done'])
                report['unchecked']+=len(row['done'])-sum(row['done'])
            else:
                report['unknown']+=len(row['done'])
        return report

def format_report(report):
    lines=[f"7日間のまとめ：{report['start']} 〜 {report['end']}（日本時間）",'',
           '各日の最後に保存した計画だけを集計しています。',
           f"計画を保存した日：{report['planned_days']} / 7日",
           f"完了チェックあり：{report['completed']}件 / チェック未完了：{report['unchecked']}件",
           f"チェック記録なし：{report['unknown']}件",
           f"計画した時間の合計：{report['planned_minutes']}分（実際の作業時間ではありません）",
           f"振り返りがある日：{report['reflection_days']}日",'',
           'チェック記録のない行動は、実際に終わったかどうか不明です。',
           '振り返りは保存された原文です。AIによる評価や要約ではありません。']
    for item in report['days']:
        lines.extend(['','─'*24,item['date']])
        row=item['row']
        if row is None:
            lines.append('計画の保存なし'); continue
        lines.append(row['plan']['goal'])
        for task,done in zip(row['plan']['tasks'],row['done']):
            status=('完了' if done else 'チェック未完了') if row['recorded'] else 'チェック記録なし'
            lines.append(f"・［{status}］{task['title']}（予定 {task['minutes']}分）")
        lines.extend(['振り返り：',row.get('reflection') or '保存なし'])
    return '\n'.join(lines)
