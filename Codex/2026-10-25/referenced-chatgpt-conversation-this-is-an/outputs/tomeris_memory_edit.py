from copy import deepcopy
import hashlib
import json
import unicodedata
from tomeris_settings import DesktopService as SettingsService
from tomeris_memory_engine import timestamp


def revision(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()

class DesktopService(SettingsService):
    def find_memories(self, query='', offset=0):
        if not isinstance(query,str) or len(query)>200:
            raise ValueError('検索語は200文字以内にしてください。')
        if type(offset) is not int or offset<0: raise ValueError('ページが不正です。')
        terms=unicodedata.normalize('NFKC',query).casefold().split()
        rows=[]
        for item in reversed(self.store.data['memories']):
            if not isinstance(item,dict) or not isinstance(item.get('text'),str): continue
            hay=unicodedata.normalize('NFKC',str(item.get('category',''))+' '+item['text']+' '+str(item.get('id',''))).casefold()
            if all(term in hay for term in terms):
                row=deepcopy(item); row['_revision']=revision(item); rows.append(row)
        total=len(rows); offset=min(offset,max(0,((total-1)//50)*50))
        return dict(query=query,offset=offset,total=total,page_size=50,rows=rows[offset:offset+50])

    def edit_memory(self, memory_id, expected_revision, text):
        if not isinstance(text,str) or not text.strip() or len(text.strip())>10000:
            raise ValueError('本文は1〜10000文字で入力してください。')
        text=text.strip()
        matches=[r for r in self.store.data['memories'] if isinstance(r,dict) and r.get('id')==memory_id]
        if len(matches)!=1: raise ValueError('記憶を一意に確認できません。開き直してください。')
        row=matches[0]
        if revision(row)!=expected_revision: raise ValueError('記憶が更新されています。閉じて検索し直してください。')
        history=row.get('edit_history',[])
        if not isinstance(history,list): raise ValueError('変更履歴の形式を確認できないため保存しませんでした。')
        if text==row.get('text'): return '変更はありません。'
        normalized=lambda s: ''.join(s.split()).casefold()
        if any(r is not row and isinstance(r,dict) and isinstance(r.get('text'),str) and normalized(r['text'])==normalized(text) for r in self.store.data['memories']):
            raise ValueError('同じ内容の記憶がすでにあります。')
        def save():
            now=timestamp()
            row.setdefault('edit_history',[]).append({'text':row['text'],'category':row.get('category',''),'replaced_at':now})
            row['text']=text; row['updated_at']=now
            self.store.save()
        self.mutate(save)
        return '記憶を修正しました。修正前の文章は変更履歴に残しています。'
