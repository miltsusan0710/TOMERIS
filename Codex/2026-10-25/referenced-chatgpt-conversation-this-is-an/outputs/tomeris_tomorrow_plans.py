"""Reviewed tomorrow carry-forward; no automatic plan writes."""
from copy import deepcopy
from datetime import date,timedelta,datetime,timezone
import json,os,tempfile,secrets,hashlib
from tomeris_dated_schedule import DesktopService as BaseService
from tomeris_plans import today,validate

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.tomorrow_drafts={}
    def plan_stamp(self):
        # Both plan and completion changes invalidate an open review.
        digest=hashlib.sha256()
        for name in ('daily_plans.json','plan_progress.json'):
            path=self.data_dir/name
            digest.update(name.encode());digest.update(path.read_bytes() if path.exists() else b'')
        return digest.hexdigest()
    def tomorrow_draft(self,identifier):
        rows=self.plan_history()
        row=next((r for r in rows if r['id']==identifier),None)
        if row is None or not row['latest']:raise ValueError('その日の最新の計画を選んでください。')
        base=today()
        if row['plan']['date']>base:raise ValueError('今日以前の計画を選んでください。')
        tasks=[deepcopy(t) for t,done in zip(row['plan']['tasks'],row['done']) if not done]
        if not tasks:raise ValueError('引き継げる行動はありません。すべて完了しています。')
        target=(date.fromisoformat(base)+timedelta(days=1)).isoformat()
        existing=any(r['plan']['date']==target for r in rows)
        draft=dict(token=secrets.token_hex(16),base=base,date=target,goal=row['plan']['goal'],tasks=tasks,recorded=row['recorded'],existing=existing,stamp=self.plan_stamp())
        # Only the most recent open review is valid, preventing stale duplicate dialogs.
        self.tomorrow_drafts={draft['token']:deepcopy(draft)}
        return deepcopy(draft)
    def save_tomorrow_draft(self,token,indices):
        draft=self.tomorrow_drafts.get(token)
        if draft is None:raise ValueError('下書きを開き直してください。保存済みの下書きは再保存できません。')
        if today()!=draft['base'] or self.plan_stamp()!=draft['stamp']:raise ValueError('日付または計画が変わりました。下書きを開き直してください。')
        if not isinstance(indices,list) or not indices or any(type(i) is not int or not 0<=i<len(draft['tasks']) for i in indices) or len(set(indices))!=len(indices):raise ValueError('引き継ぐ行動を選んでください。')
        tasks=[draft['tasks'][i] for i in indices]
        plan=validate(draft['goal'],sum(t['minutes'] for t in tasks),tasks)
        plan.update(date=draft['date'],approved_at=datetime.now(timezone.utc).isoformat())
        plans=self._plans()
        # Identical latest target plan is already sufficient; do not append duplicates.
        prior=next((p for p in reversed(plans) if p['date']==draft['date']),None)
        if prior and all(prior.get(k)==plan[k] for k in ('goal','budget','tasks')):raise ValueError('同じ内容の計画が対象日に保存されています。')
        plans.append(plan)
        fd,name=tempfile.mkstemp(prefix='daily_plans_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                json.dump(dict(version=1,plans=plans),f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
            os.replace(name,self.data_dir/'daily_plans.json')
        finally:
            if os.path.exists(name):os.unlink(name)
        self.tomorrow_drafts.pop(token,None)
        return f"{draft['date']}の計画を保存しました。元の計画と対象日の以前の計画は履歴に残っています。"
