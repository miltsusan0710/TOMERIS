"""Quarantine suspected advocacy before catalogue ingestion; never train weights."""
import hashlib,json,os,re,tempfile
from copy import deepcopy
from datetime import datetime,timezone
from tomeris_parallel_research_v086 import DesktopService as BaseService
from tomeris_web_search import public_url

def reasons(text):
    text=text.casefold()
    patterns=[('暴力・テロの推奨の疑い',r'(?:暴力|テロ|殺害|虐殺|爆破).{0,50}(?:推奨|正当化|すべき|呼びかけ|実行せよ|奨励|支持|称賛)'),
              ('差別・迫害の扇動の疑い',r'(?:人種|民族|宗教|障害者|移民|同性愛).{0,50}(?:排除すべき|追放せよ|劣等|迫害|抹殺|殺せ)'),
              ('暴力・迫害の扇動の疑い',r'(?:殺せ|皆殺し|抹殺せよ|虐殺せよ)'),
              ('英語の暴力・差別扇動の疑い',r'(?:advocate|encourage|justify|promote).{0,60}(?:terrorism|racial violence|genocide)|(?:kill|exterminate|expel) all .{0,40}(?:immigrants|jews|muslims|christians)')]
    return [label for label,pattern in patterns if re.search(pattern,text)]

def fingerprint(item):
    return hashlib.sha256(json.dumps(item,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def snapshot(item):
    page=item['page']
    if not public_url(page.get('url','')) or not isinstance(page.get('text'),str):raise ValueError('資料の形式が不正です。')
    if len(page['text'])>100000:raise ValueError('確認対象の本文が大きすぎます。')
    if not isinstance(item.get('excerpts'),list) or len(item['excerpts'])>20:raise ValueError('引用の形式が不正です。')
    result=dict(page={k:page.get(k,'') for k in ('title','url','text','published','updated','provider')},excerpts=list(item['excerpts']))
    if not all(isinstance(v,str) for v in result['page'].values()) or not all(isinstance(q,str) and q in page['text'] for q in result['excerpts']):raise ValueError('引用の一致を確認できません。')
    return result

class ReviewCatalogue:
    def __init__(self,base,path):
        object.__setattr__(self,'_base',base);object.__setattr__(self,'review_path',path)
        object.__setattr__(self,'review_rows',{});object.__setattr__(self,'review_error','')
        try:
            if path.exists():
                if path.stat().st_size>12000000:raise ValueError()
                value=json.loads(path.read_text(encoding='utf-8'))
                if value.get('version')!=1 or not isinstance(value.get('rows'),dict) or len(value['rows'])>100:raise ValueError()
                for ident,row in value['rows'].items():
                    if row['status'] not in ('pending','approved','rejected') or fingerprint(snapshot(row['item']))!=ident:raise ValueError()
                self.review_rows=value['rows']
        except (ValueError,OSError,KeyError,TypeError,AttributeError):self.review_error='確認記録を読めません。新しい資料の取り込みを停止し、元ファイルを保持しています。'
    def __getattr__(self,name):return getattr(self._base,name)
    def __setattr__(self,name,value):
        if name.startswith('review_'):object.__setattr__(self,name,value)
        else:setattr(self._base,name,value)
    def commit(self,rows):
        if self.review_error:raise ValueError(self.review_error)
        encoded=json.dumps(dict(version=1,rows=rows),ensure_ascii=False)
        if len(encoded.encode('utf-8'))>12000000:raise ValueError('確認記録の容量上限です。この資料は取り込みません。')
        fd,path=tempfile.mkstemp(dir=self.review_path.parent,prefix='review_',suffix='.tmp')
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                f.write(encoded);f.flush();os.fsync(f.fileno())
            os.replace(path,self.review_path);self.review_rows=rows
        finally:
            if os.path.exists(path):os.unlink(path)
    def learn(self,items):
        if self.review_error or not self.enabled:return 0
        count=0
        for raw in items:
            item=snapshot(raw);why=reasons(item['page']['title']+'\n'+item['page']['text'])
            ident=fingerprint(item);existing=self.review_rows.get(ident)
            if existing and existing['status']=='rejected':continue
            if why and (not existing or existing['status']!='approved'):
                if not existing and len(self.review_rows)<100:
                    rows=deepcopy(self.review_rows)
                    rows[ident]=dict(item=item,reasons=why,status='pending',retrieved=datetime.now(timezone.utc).isoformat())
                    self.commit(rows)
                # A full queue never permits an unchecked item. Safe items continue.
                continue
            count+=self._base.learn([item])
        return count
    def decide(self,ident,approved):
        row=self.review_rows.get(ident)
        if row is None or row['status']!='pending':raise ValueError('確認待ちの資料を選び直してください。')
        rows=deepcopy(self.review_rows);rows[ident]['status']='approved' if approved else 'rejected'
        self.commit(rows)
        if approved:self._base.learn([row['item']])
        return 'この版の資料を参照候補として許可しました。内容への賛同や正しさの認定ではありません。' if approved else 'この版の資料を取り込まない設定にしました。別の内容の収集を続けます。'

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.catalogue=ReviewCatalogue(self.catalogue,self.data_dir/'learning_review.json')
        self.methods.catalogue=self.catalogue
    def eligible_topics(self):
        pending={row['item']['page']['title'] for row in getattr(self.catalogue,'review_rows',{}).values() if row['status']=='pending'}
        return [topic for topic in super().eligible_topics() if topic not in pending]
    def collect_public_topic(self):
        result=super().collect_public_topic()
        if result:
            pending=sum(r['status']=='pending' for r in self.catalogue.review_rows.values())
            if pending:result+=f'\n確認待ち資料 {pending}件は取り込んでいません。「資料学習 → 確認待ちの資料」で確認できます。別の内容の収集は続けます。'
            if len(self.catalogue.review_rows)>=100:result+='\n確認記録の上限100件に達しました。新たな疑わしい資料は取り込みません。'
            if self.catalogue.review_error:result+='\n'+self.catalogue.review_error
        return result
