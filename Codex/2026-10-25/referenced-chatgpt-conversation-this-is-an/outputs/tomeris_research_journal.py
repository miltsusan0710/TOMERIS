"""Bounded research metadata journal. No page text, keys, or generated answers."""
import json,os,tempfile,uuid
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
from tomeris_web_search import public_url

MAX_BYTES=2_000_000
MAX_ROWS=100

def validate(data):
    if not isinstance(data,dict) or data.get('version')!=1 or type(data.get('version')) is not int or not isinstance(data.get('records'),list) or len(data['records'])>MAX_ROWS:
        raise ValueError('調査履歴の形式を確認してください。')
    seen=set()
    for row in data['records']:
        if not isinstance(row,dict) or set(row)!= {'id','question','retrieved_at','method','sources'}:raise ValueError('調査履歴の項目が不正です。')
        for key,limit in [('id',32),('question',2000),('retrieved_at',80),('method',100)]:
            if not isinstance(row[key],str) or not 1<=len(row[key])<=limit:raise ValueError('調査履歴の文字列が不正です。')
        identifier=row['id']
        if len(identifier)!=32 or any(c not in '0123456789abcdef' for c in identifier) or identifier in seen:raise ValueError('調査履歴の識別子が不正です。')
        seen.add(identifier)
        try:stamp=datetime.fromisoformat(row['retrieved_at'])
        except ValueError:raise ValueError('調査履歴の日付が不正です。') from None
        if stamp.tzinfo is None:raise ValueError('調査履歴の日付に時差がありません。')
        if not isinstance(row['sources'],list) or not 1<=len(row['sources'])<=3:raise ValueError('調査履歴の出典数が不正です。')
        urls=set()
        for source in row['sources']:
            if not isinstance(source,dict) or set(source)!={'title','url'}:raise ValueError('調査履歴の出典が不正です。')
            title,url=source['title'],source['url']
            if not isinstance(title,str) or not 1<=len(title)<=300:raise ValueError('出典名が不正です。')
            if not isinstance(url,str) or len(url)>3000 or any(c.isspace() for c in url) or not public_url(url) or url in urls:raise ValueError('出典URLが不正です。')
            urls.add(url)
    return data

class ResearchJournal:
    def __init__(self,directory):self.path=Path(directory)/'research_history.json'
    def read(self):
        if not self.path.exists():return []
        if self.path.stat().st_size>MAX_BYTES:raise ValueError('調査履歴が容量上限を超えています。')
        raw=self.path.read_bytes()
        if len(raw)>MAX_BYTES:raise ValueError('調査履歴が容量上限を超えています。')
        return deepcopy(validate(json.loads(raw.decode('utf-8')))['records'])
    def write(self,rows):
        raw=json.dumps(validate(dict(version=1,records=rows)),ensure_ascii=False,indent=2).encode('utf-8')
        if len(raw)>MAX_BYTES:raise ValueError('調査履歴が容量上限を超えています。')
        fd,name=tempfile.mkstemp(prefix='research_history_',suffix='.tmp',dir=self.path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)
    def append(self,question,method,sources,retrieved_at=None):
        rows=self.read() # Corrupt existing files must not be silently replaced.
        row=dict(id=uuid.uuid4().hex,question=question,method=method,sources=deepcopy(sources),retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat())
        validate(dict(version=1,records=[row]))
        self.write((rows+[row])[-MAX_ROWS:])
        return deepcopy(row)
    def get(self,identifier):
        row=next((r for r in self.read() if r['id']==identifier),None)
        if row is None:raise ValueError('調査履歴が見つかりません。読み直してください。')
        return row
    def delete(self,identifier):
        rows=self.read();kept=[r for r in rows if r['id']!=identifier]
        if len(kept)==len(rows):raise ValueError('調査履歴が見つかりません。読み直してください。')
        self.write(kept)
