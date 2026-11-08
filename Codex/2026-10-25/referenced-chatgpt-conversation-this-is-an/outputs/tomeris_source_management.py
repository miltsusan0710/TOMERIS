"""Search and selectively remove source records; checks never certify facts."""
import hashlib,json
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from tomeris_research_learning import DesktopService as BaseService
from tomeris_source_catalogue import Catalogue
from tomeris_catalogue_schema import validate_catalogue,MAX_SOURCE_BYTES
from tomeris_page_reader import fetch_page,PageError

def revision(row):return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
class CheckedCatalogue(Catalogue):
    def __init__(self,directory):
        super().__init__(directory)
        if not self.error:
            try:validate_catalogue(dict(version=1,enabled=self.enabled,rows=self.rows))
            except ValueError:self.error='保存資料の形式を確認できないため学習を停止しました。元ファイルは保持しています。';self.enabled=False;self.rows=[]
    def save(self,rows,enabled):
        value=dict(version=1,enabled=enabled,rows=rows)
        validate_catalogue(value)
        if len(json.dumps(value,ensure_ascii=False).encode('utf-8'))>MAX_SOURCE_BYTES:raise ValueError('保存資料の容量上限を超えています。')
        return super().save(rows,enabled)

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.catalogue=CheckedCatalogue(self.data_dir);self.methods.catalogue=self.catalogue;self.source_checks={}
    def source_records(self,query=''):
        if not isinstance(query,str) or len(query)>200:raise ValueError('検索語は200文字以内にしてください。')
        words=query.casefold().split();rows=[]
        for row in reversed(self.catalogue.rows):
            if not all(word in (row['title']+' '+row['url']+' '+row['excerpt']).casefold() for word in words):continue
            item=deepcopy(row);item['revision']=revision(row);item['check']=self.source_checks.get(row['url'],'この起動中の再取得確認は未実施')
            rows.append(item)
        return dict(rows=rows,total=len(self.catalogue.rows),enabled=self.catalogue.enabled,error=self.catalogue.error)
    def selected_source(self,url,expected):
        if self.catalogue.error:raise ValueError(self.catalogue.error)
        rows=[r for r in self.catalogue.rows if r['url']==url]
        if len(rows)!=1 or revision(rows[0])!=expected:raise ValueError('資料が変更または消去されています。一覧を読み直してください。')
        return rows[0]
    def remove_source(self,url,expected):
        self.selected_source(url,expected)
        self.catalogue.save([r for r in self.catalogue.rows if r['url']!=url],self.catalogue.enabled)
        self.source_checks.pop(url,None)
        return '選択した保存資料だけを消去しました。再度調査すると保存される場合があります。'
    def check_source(self,url,expected):
        self.selected_source(url,expected)
        stamp=datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
        if self.demo:return '画面確認用：ネットへの再取得は実行していません。'
        try:
            page=fetch_page(url)
            if not page.get('text','').strip():raise PageError('本文が空です。')
            status=stamp+' 再取得成功（内容の一致・正確さは未検証）\n取得先：'+page['url']
        except PageError as exc:status=stamp+' 再取得失敗：'+str(exc)
        self.source_checks[url]=status
        return status+'\n保存本文と取得日時は変更していません。'
