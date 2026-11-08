from pathlib import Path
p=Path('outputs/tomeris_auto_research.py')
s=p.read_text(encoding='utf-8-sig')
a=s.index('def instruction(text):');b=s.index('\nclass AutoMethods',a)
s=s[:a]+'''def instruction(text):
    text=text.strip()
    # Do not interpret negation or conflicting provider instructions as permission to use the first provider.
    if re.search(r'('+NAMES+r')(?:で(?:は)?なく|以外|を使わず|を使わない)',text,re.I):
        return '要確認',text
    directive=r'('+NAMES+r')(?:だけ)?(?:で(?!き)|を使って|を使い|から)'
    found=list(re.finditer(directive,text,re.I))
    if len({MAP[m[1].lower()] for m in found})>1:return '要確認',text
    start=re.match(r'^'+directive+r'[、,\\s]*(.*)$',text,re.I)
    end=re.match(r'^(.*?)[を、,\\s]*('+NAMES+r')(?:だけ)?(?:で|を使って)(?:調べて|検索して|調査して)(?:ください)?[。！!？?]*$',text,re.I)
    if start:return MAP[start[1].lower()],start[2].strip()
    if end:return MAP[end[2].lower()],end[1].strip()
    return None,text


def missing_topic(text):
    return not text or bool(re.fullmatch(r'(?:検索|調査|調べて|検索して|調査して|探して)(?:ください)?[。！!？?]*',text))
''' +s[b:]
s=s.replace("self.mode='自動'", "self.mode='自動';self.question_context=''",1)
s=s.replace("比較|おすすめ',text)","比較|おすすめ',self.question_context or text)")
s=s.replace("self.methods=AutoMethods()", "self.methods=AutoMethods();self.pending_method=None")
s=s.replace("if instruction(text)[0]:return self.report(text,model=model)","if instruction(text)[0] or self.pending_method:return self.report(text,model=model)")
s=s.replace("if instruction(question)[0]:return self.report(question,progress,model)","if instruction(question)[0] or self.pending_method:return self.report(question,progress,model)")
s=s.replace("        selected,topic=instruction(question)\n        if not selected:return super().report(question,progress,model)",'''        selected,topic=instruction(question)
        if question.strip() in ('キャンセル','やめる','中止'):
            self.pending_method=None;self.pending_subject=False
            return self.track(question,'調査の確認待ちを取り消しました。')
        if selected=='要確認':
            self.pending_method=None
            return self.track(question,'調査方法を一つ指定してください。例：Wikipediaでアイアンマンについて調べて。今回は外部へ送信していません。')
        if not selected and self.pending_method:
            selected=self.pending_method;self.pending_method=None
        if not selected:
            old_context=self.methods.question_context
            try:
                self.methods.question_context=question
                return super().report(question,progress,model)
            finally:self.methods.question_context=old_context''')
s=s.replace("        if not topic:return self.track(question,'指定した方法で何を調べるか入力してください。例：Googleでアイアンマンについて調べて')", "        if missing_topic(topic):\n            self.pending_method=selected\n            return self.track(question,'指定方法：'+selected+'。何を調べますか？次の入力をこの方法で調べます。取り消す場合は「キャンセル」と入力してください。')\n        self.pending_method=None")
s=s.replace("        finally:self.methods.mode=old", "        finally:\n            self.methods.mode=old\n            if self.pending_subject:self.pending_method=selected")
# Expose which method was requested even if the provider returns nothing.
s=s.replace("            return super().report(topic,progress,model)", "            return super().report(topic,progress,model)")
Path('outputs/tomeris_auto_research_v0281.py').write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_desktop_v028.py');s=p.read_text(encoding='utf-8').replace('tomeris_auto_research import','tomeris_auto_research_v0281 import').replace('v0.28','v0.28.1')
Path('outputs/tomeris_desktop_v0281.py').write_text(s,encoding='utf-8')
