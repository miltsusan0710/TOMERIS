"""Bounded source catalogue. Saved text is evidence data, never instructions."""
import json,os,tempfile
from datetime import datetime,timezone,timedelta
from tomeris_web_search import public_url
from tomeris_strict_evidence import terms,matches
class Catalogue:
    def __init__(self,directory):
        self.path=directory/'research_sources.json';self.rows=[];self.enabled=True;self.error=''
        if self.path.exists():
            try:
                if self.path.stat().st_size>1000000:raise ValueError()
                data=json.loads(self.path.read_text(encoding='utf-8'))
                if data.get('version')!=1 or type(data.get('enabled')) is not bool or not isinstance(data.get('rows'),list) or len(data['rows'])>200:raise ValueError()
                for r in data['rows']:
                    if not isinstance(r,dict) or not all(isinstance(r.get(k),str) for k in ('url','title','excerpt','retrieved')) or not public_url(r['url']):raise ValueError()
                self.rows=data['rows'];self.enabled=data['enabled']
            except (OSError,ValueError,AttributeError):self.error='学習資料を読めなかったため、元ファイルを保持して資料学習を停止しています。';self.enabled=False
    def save(self,rows,enabled):
        if self.error:raise ValueError(self.error)
        fd,name=tempfile.mkstemp(prefix='research_sources_',suffix='.tmp',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                json.dump(dict(version=1,enabled=enabled,rows=rows),f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)
        self.rows=rows;self.enabled=enabled
    def learn(self,items):
        if not self.enabled:return 0
        rows=list(self.rows);count=0
        for item in items:
            page=item['page'];url=page['url']
            if not public_url(url):continue
            rows=[r for r in rows if r['url']!=url]
            rows.append(dict(url=url,title=page.get('title','')[:300],excerpt='\n'.join(item['excerpts'])[:1200],retrieved=datetime.now(timezone(timedelta(hours=9))).isoformat()))
            count+=1
        if count:self.save(rows[-200:],self.enabled)
        return count
    def candidates(self,query):
        if not self.enabled:return []
        anchors=terms(query)
        return [dict(title=r['title'],url=r['url'],snippet=r['excerpt'],provider='保存資料の再取得候補') for r in reversed(self.rows) if matches(r['title']+' '+r['excerpt'],anchors)][:2]
    def summary(self):
        if self.error:return self.error
        return ('資料学習：有効' if self.enabled else '資料学習：停止中')+f' / {len(self.rows)}件\n保存資料は未検証です。次の調査ではページを再取得します。\n'+'\n\n'.join(r['title']+'\n'+r['url']+'\n取得：'+r['retrieved'] for r in self.rows[-10:])
