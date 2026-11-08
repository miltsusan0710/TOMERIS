"""School location questions require retrieved evidence, never model guesses."""
import re
from datetime import datetime,timezone,timedelta
from tomeris_adaptive_collection import DesktopService as BaseService
from tomeris_auto_research_v029 import instruction
from tomeris_page_reader import fetch_page

# Verified official access pages, not cached addresses. Read afresh for each question.
SCHOOLS={
 '荒川区立第一中学校':('荒川区立第一中学校','https://www.aen.arakawa.tokyo.jp/ARAKAWA-1-J/outline/1005143.html'),
 '本所高校':('東京都立本所高等学校','https://www.metro.ed.jp/honjo-h/access/access.html'),
 '本所高等学校':('東京都立本所高等学校','https://www.metro.ed.jp/honjo-h/access/access.html'),
 '東京都立本所高等学校':('東京都立本所高等学校','https://www.metro.ed.jp/honjo-h/access/access.html')}

def subject(text):
    match=re.fullmatch(r'([^\s「」"\n]{1,60}(?:小学校|中学校|高等学校|高校|大学|専門学校))(?:は|って|の)?(?:どこ(?:にある|にありますか|ですか)?|所在地(?:は|を教えて)?|住所(?:は|を教えて)?|場所(?:は|を教えて)?)[？?。！!]*',text.strip())
    return match[1] if match else None

class DesktopService(BaseService):
    def school_location(self,text,model=None,progress=None):
        method,phrase=instruction(text)
        name=subject(phrase)
        if not name:return None
        self.clear_tool_context()
        if method or self.methods.mode!='自動':return self.report(text,progress,model)
        if name not in SCHOOLS:return self.report(name+' 所在地 公式',progress,model)
        full,url=SCHOOLS[name]
        if self.demo:return self.track(text,'画面確認用：学校の所在地は取得していません。')
        if progress:progress('学校の公式アクセスページを確認しています…')
        try:
            page=fetch_page(url);body=page['text']
            if page.get('url')!=url:raise ValueError('登録した公式ページから移動しています。')
            title_name='第一中学校' if full=='荒川区立第一中学校' else full
            if full not in body and title_name not in page.get('title',''):raise ValueError('対象校の一致を確認できません。')
            # Keep the entire short source line, not synthesized address fragments.
            lines=[line.strip() for line in body.splitlines() if len(line.strip())<=220 and re.search(r'東京都[^\s<]{1,20}[区市郡][^\s<]{1,25}[0-9０-９]',line) and not re.search(r'校長|電話|FAX|ファクス',line,re.I)]
            if not lines:raise ValueError('住所の記述を読み取れませんでした。')
            answer=full+'の所在地です。\n'+lines[0]+'\n\n出典：学校の公式アクセスページ\n'+page.get('url',url)
            answer+='\n取得：'+datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
        except (OSError,ValueError,KeyError):
            answer=full+'の所在地を今回の本文取得で確認できませんでした。住所を推測せず、公式ページをご案内します。\n'+url
        return self.track(text,answer)
    def chat(self,text,model,use_memory=False):
        answer=self.school_location(text,model)
        return answer if answer is not None else super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        answer=self.school_location(question,model,progress)
        return answer if answer is not None else super().web_chat(question,model,use_memory,automatic,progress)
