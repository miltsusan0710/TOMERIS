from pathlib import Path
p=Path('outputs/tomeris_auto_research_v0281.py');s=p.read_text(encoding='utf-8')
s=s.replace('import webbrowser','import webbrowser\nfrom datetime import datetime\nfrom tomeris_page_reader import fetch_page, PageError\nfrom tomeris_strict_evidence import terms\nfrom urllib.parse import urlsplit')
s=s.replace("        if not selected:\n            old_context", "        if not selected and re.fullmatch(r'https?://[^\\s<>「」]+',question.strip()):\n            return self.read_direct_url(question.strip())\n        if not selected:\n            old_context")
s=s.replace("        self.pending_weather=None;self.pending_subject=False", "        if self.pending_subject and re.search(r'アイアンマン|マーベル|marvel|iron.?man',topic,re.I):\n            topic='マーベル アイアンマン JARVIS ジャービス'\n        self.pending_weather=None;self.pending_subject=False")
s=s.replace("        self.pending_method=None\n        if self.demo", "        self.pending_method=None\n        if selected.startswith('Wikipedia') and re.search(r'https?://',topic):\n            return self.track(question,'Wikipediaで検索する対象名を入力してください。URL本文を直接読む場合は、方法の指定を外してURLを送ってください。')\n        if self.demo")
s+='''
    def read_direct_url(self,url):
        self.pending_weather=None;self.pending_subject=False
        if self.demo:return self.track(url,'画面確認用：指定URLの本文は取得していません。')
        try:page=fetch_page(url)
        except PageError as exc:return self.track(url,'指定URLの本文を取得できませんでした。\\n'+str(exc))
        excerpt=page['text'].strip()[:1800]
        if not excerpt:return self.track(url,'指定URLから本文を取得できませんでした。')
        answer='指定URLの本文（冒頭・最大1800文字）\\n'+page.get('title','')+'\\n'+page['url']+'\\n\\n'+excerpt+'\\n\\n本文を取得した結果です。事実確認や質問への回答はまだ行っていません。詳しく確認したい点を、対象名とURLを添えて入力してください。'
        return self.save_answer(url,answer)
'''
p.write_text(s,encoding='utf-8')
