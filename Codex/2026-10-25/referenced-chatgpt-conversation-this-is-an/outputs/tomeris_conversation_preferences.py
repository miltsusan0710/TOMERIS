"""Explicit conversational preferences, stored with editable memory history."""
import re
from tomeris_location_guard import DesktopService as BaseService
from tomeris_memory_edit import revision

STYLES={'回答は短く、結論から。':'回答は短く、結論から伝えてください。','回答は詳しく、例を添えて。':'回答は具体的な説明と必要な例を添えてください。','会話の好みは標準。':''}

def conversation_style(store):
    rows=[r for r in store.data['memories'] if isinstance(r,dict) and r.get('category')=='会話の好み' and r.get('text') in STYLES]
    return STYLES[rows[-1]['text']] if rows else ''

class DesktopService(BaseService):
    def learn_preference(self,text):
        compact=text.strip().rstrip('。！!')
        if compact in ('覚えた会話の好みを教えて','会話の好みを教えて'):
            return self.track(text,'保存している会話の好み：'+(conversation_style(self.store) or '標準です。'))
        value=None
        if re.fullmatch(r'(?:今後は|これからは|いつも)?(?:回答|返答|説明)(?:は|を)(?:短く|簡潔に)(?:して|してください|お願い|お願いします)',compact):value='回答は短く、結論から。'
        elif re.fullmatch(r'(?:今後は|これからは|いつも)?(?:回答|返答|説明)(?:は|を)詳しく(?:して|してください|お願い|お願いします)',compact):value='回答は詳しく、例を添えて。'
        elif compact in ('会話の好みをリセット','会話の好みを標準に戻して'):value='会話の好みは標準。'
        if value is None:return None
        rows=[r for r in self.store.data['memories'] if isinstance(r,dict) and r.get('category')=='会話の好み' and r.get('text') in STYLES]
        if rows:
            row=rows[-1]
            if row['text']!=value:self.edit_memory(row['id'],revision(row),value)
        else:self.remember(value,'会話の好み')
        return self.track(text,'会話の好みを覚えました。'+value+'\n次の通常会話から反映します。「会話の好みを教えて」で確認、「会話の好みをリセット」で標準に戻せます。')
    def chat(self,text,model,use_memory=False):
        answer=self.learn_preference(text)
        return answer if answer is not None else super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        answer=self.learn_preference(question)
        return answer if answer is not None else super().web_chat(question,model,use_memory,automatic,progress)
