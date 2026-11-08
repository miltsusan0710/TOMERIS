"""Literal keyword search over locally saved question/answer pairs."""
import unicodedata
from tomeris_restore import DesktopService as RestoreService

PAGE_SIZE=50

def normalize(text):
    return unicodedata.normalize('NFKC',text).casefold()

class DesktopService(RestoreService):
    def find_conversations(self,query='',offset=0):
        if not isinstance(query,str) or len(query)>200:
            raise ValueError('検索語は200文字以内で入力してください。')
        if type(offset) is not int or offset<0:
            raise ValueError('表示する位置が不正です。')
        terms=normalize(query).split()
        records=self.store.data.get('conversations',[])
        if not isinstance(records,list):
            raise ValueError('会話履歴の形式を確認してください。')
        matches=[]
        for index in range(len(records)-1,-1,-1):
            item=records[index]
            if not isinstance(item,dict): continue
            question=item.get('user',''); answer=item.get('tomeris','')
            question=question if isinstance(question,str) else ''
            answer=answer if isinstance(answer,str) else ''
            if not question and not answer: continue
            text=normalize(question+'\n'+answer)
            if all(term in text for term in terms):
                stamp=item.get('timestamp','')
                matches.append({'index':index,'timestamp':stamp if isinstance(stamp,str) else '',
                                'user':question,'tomeris':answer})
        total=len(matches)
        offset=min(offset,((total-1)//PAGE_SIZE)*PAGE_SIZE) if total else 0
        return {'query':query,'offset':offset,'total':total,'page_size':PAGE_SIZE,
                'rows':matches[offset:offset+PAGE_SIZE]}
