"""Explicitly saved plan reflections, separate from memory and completion."""
from datetime import datetime, timezone
import json
import os
import tempfile
from tomeris_plan_carry import DesktopService as CarryService
from tomeris_plan_history import describe as describe_plan

class DesktopService(CarryService):
    def _reflections(self):
        path=self.data_dir/'plan_reflections.json'
        if not path.exists():
            return {'version':1,'plans':{}}
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('plans'),dict):
            raise ValueError('振り返り記録の形式が不正です。記録は変更しません。')
        for records in data['plans'].values():
            if not isinstance(records,list) or not records:
                raise ValueError('振り返り記録を読み取れません。')
            for item in records:
                if not isinstance(item,dict) or not isinstance(item.get('text'),str) or not 1<=len(item['text'].strip())<=2000:
                    raise ValueError('振り返り記録の内容が不正です。')
        return data
    def plan_history(self):
        rows=super().plan_history(); saved=self._reflections()['plans']
        for row in rows:
            records=saved.get(row['id'],[])
            row['reflection']=records[-1]['text'] if records else ''
        return rows
    def get_reflection(self,identifier):
        row=next((row for row in super().plan_history() if row['id']==identifier),None)
        if row is None:
            raise ValueError('対象の計画が見つかりません。履歴を読み直してください。')
        records=self._reflections()['plans'].get(identifier,[])
        return {'id':identifier,'goal':row['plan']['goal'],'date':row['plan']['date'],
                'revision':len(records),'text':records[-1]['text'] if records else ''}
    def save_reflection(self,identifier,text,expected_revision):
        if not isinstance(text,str) or not 1<=len(text.strip())<=2000:
            raise ValueError('振り返りは1〜2000文字で入力してください。')
        current=self.get_reflection(identifier)
        if type(expected_revision) is not int or current['revision']!=expected_revision:
            raise ValueError('保存された振り返りが変わりました。入力を控えてから画面を開き直してください。')
        text=text.strip()
        if text==current['text']:
            return current
        data=self._reflections()
        data['plans'].setdefault(identifier,[]).append({'text':text,'saved_at':datetime.now(timezone.utc).isoformat()})
        path=self.data_dir/'plan_reflections.json'
        fd,name=tempfile.mkstemp(prefix='plan_reflections_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as handle:
                json.dump(data,handle,ensure_ascii=False,indent=2)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(name,path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return {**current,'text':text,'revision':current['revision']+1}

def describe(row):
    return describe_plan(row)+'\n\n【振り返り】\n'+(row.get('reflection') or 'まだ保存されていません。')
