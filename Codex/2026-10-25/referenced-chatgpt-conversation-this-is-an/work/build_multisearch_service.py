from pathlib import Path
s=Path('outputs/tomeris_evidence_report_v0261.py').read_text(encoding='utf-8-sig')
s=s.replace('from tomeris_strict_evidence import terms,passages,relevance_score','from tomeris_strict_evidence import terms,passages,relevance_score\nfrom tomeris_search_methods import SearchMethods,MethodError,wikipedia_page,search_topic\nfrom tomeris_google_grounding import google_search,save_grounding')
s=s.replace('super().__init__(*args,**kwargs);self.pending_subject=False','super().__init__(*args,**kwargs);self.pending_subject=False;self.methods=SearchMethods()')
s=s.replace("(site_query(question) if site_request(question) else research_queries(question)[0])","(site_query(question) if site_request(question) else search_topic(question))")
s=s.replace("        for query in (() if direct_urls else (topic,topic+' 公式')):","        for query in (() if direct_urls else (topic,)):")
s=s.replace("            try:found=search_web(query)\n            except SearchError:failures.append('検索できなかった語：'+query);continue", "            found,notes=self.methods.candidates(query)\n            failures.extend(notes)")
s=s.replace("                page=fetch_page(row['url'])", "                page=wikipedia_page(row) if row.get('wiki_id') else fetch_page(row['url'])")
s=s.replace('except PageError as exc:', 'except (PageError,MethodError) as exc:')
s=s.replace("                date='掲載日（ページの記載）：'+page['published'] if page['published'] else '掲載日：確認できませんでした'", "                date='掲載日（ページの記載）：'+page['published'] if page['published'] else '掲載日：確認できませんでした'\n                if page.get('updated'):date='記事の更新日時（提供元の記載）：'+page['updated']\n                if page.get('provider'):date+='\\n資料種別：'+page['provider']")
s=s.replace("【取得できなかったもの】","【使用した方法・取得状況】")
# Optional Google calls are explicit in the research-methods dialog only.
s+='''
    def configure_methods(self,mode,brave_key,gemini_key,gemini_model):
        self.methods.configure(mode,brave_key,gemini_key,gemini_model)
        return '調査方法を変更しました。この起動中のみ有効です。APIキーはファイルに保存しません。'
    def google_grounded_report(self,question):
        if self.demo:raise MethodError('画面確認用モードではGoogle APIに接続しません。')
        value=google_search(question,self.methods.gemini_key,self.methods.gemini_model)
        return save_grounding(value,question,self.data_dir/'google_reports')
'''
Path('outputs/tomeris_multisearch_service.py').write_text(s,encoding='utf-8')
