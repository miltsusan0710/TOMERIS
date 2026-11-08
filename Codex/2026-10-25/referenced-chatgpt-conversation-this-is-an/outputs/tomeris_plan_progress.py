"""Completion state stored separately; existing plan files are never rewritten."""
from copy import deepcopy
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from tomeris_plans import DesktopService as PlanService, today

class DesktopService(PlanService):
    def _progress(self):
        path=self.data_dir/'plan_progress.json'
        if not path.exists():
            return {'version':1,'plans':{}}
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('plans'),dict):
            raise ValueError('完了記録を読み取れません。既存の記録は変更しません。')
        for key,item in data['plans'].items():
            if not isinstance(key,str) or not isinstance(item,dict) or not isinstance(item.get('done'),list) or not 1<=len(item['done'])<=3 or any(type(flag) is not bool for flag in item['done']):
                raise ValueError('完了記録の形式が不正です。既存の記録は変更しません。')
        return data
    def today_plan(self):
        candidates=[(i,p) for i,p in enumerate(self._plans()) if p['date']==today()]
        if not candidates:
            return None
        index,plan=candidates[-1]
        identifier=hashlib.sha256(json.dumps([index,plan],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
        progress=self._progress()['plans'].get(identifier)
        flags=progress['done'] if progress else [False]*len(plan['tasks'])
        if len(flags)!=len(plan['tasks']):
            raise ValueError('計画と完了記録が一致しません。記録は変更しません。')
        return {'id':identifier,'plan':deepcopy(plan),'done':list(flags)}
    def set_completion(self,identifier,index,done):
        current=self.today_plan()
        if current is None or current['id']!=identifier:
            raise ValueError('日付または計画が変わりました。「読み直す」を押してください。')
        if type(index) is not int or not 0<=index<len(current['done']) or type(done) is not bool:
            raise ValueError('完了チェックの指定が不正です。')
        data=self._progress()
        current['done'][index]=done
        data['plans'][identifier]={'done':current['done'],'updated_at':datetime.now(timezone.utc).isoformat()}
        path=self.data_dir/'plan_progress.json'
        fd,name=tempfile.mkstemp(prefix='plan_progress_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as handle:
                json.dump(data,handle,ensure_ascii=False,indent=2)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(name,path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return current
