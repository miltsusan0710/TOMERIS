"""Optional Gemini Google Search response, rendered separately with original citations."""
from html import escape
from pathlib import Path
import tempfile
from tomeris_search_methods import json_request,MethodError
from tomeris_web_search import public_url


def google_search(query,key,model):
    if not key:raise MethodError('Gemini APIキー未設定です。')
    if not query.strip() or len(query)>2000:raise MethodError('Google APIへの質問は1〜2000文字にしてください。')
    payload={'model':model,'input':query,'tools':[{'type':'google_search'}]}
    return json_request('https://generativelanguage.googleapis.com/v1beta/interactions',headers={'x-goog-api-key':key},payload=payload,timeout=90)

def render_grounding(data,question):
    steps=data.get('steps',[])
    if data.get('status') in ('failed','cancelled','in_progress') or not isinstance(steps,list):raise MethodError('Googleの検索回答が完了していません。')
    searched=any(isinstance(step,dict) and step.get('type')=='google_search_call' for step in steps)
    if not searched:raise MethodError('Google検索の実行を応答内で確認できませんでした。未確認のAI回答を報告として表示しません。')
    sources=[];blocks=[];widgets=[]
    for step in steps:
        if not isinstance(step,dict):continue
        if step.get('type')=='google_search_result':
            for item in step.get('result',[]) if isinstance(step.get('result'),list) else []:
                widget=item.get('search_suggestions') if isinstance(item,dict) else None
                if isinstance(widget,str) and len(widget)<100000:widgets.append(widget)
        if step.get('type')!='model_output':continue
        for block in step.get('content',[]) if isinstance(step.get('content'),list) else []:
            if not isinstance(block,dict) or block.get('type')!='text':continue
            text=block.get('text');annotations=block.get('annotations',[])
            if not isinstance(text,str) or len(text)>50000 or not isinstance(annotations,list):continue
            markers={}
            for a in annotations:
                if not isinstance(a,dict) or a.get('type')!='url_citation' or not public_url(a.get('url','')):continue
                start,end=a.get('start_index'),a.get('end_index')
                if type(start) is not int or type(end) is not int or not 0<=start<end<=len(text):continue
                source=(a['url'],str(a.get('title') or a['url']))
                if source not in sources:sources.append(source)
                index=sources.index(source)+1
                markers.setdefault(end,[]).append(f'<a href="#source{index}">[{index}]</a>')
            if markers:
                previous=0;parts=[]
                for end in sorted(markers):parts.append(escape(text[previous:end]));parts.extend(markers[end]);previous=end
                parts.append(escape(text[previous:]));blocks.append('<div class="answer">'+''.join(parts)+'</div>')
    if not blocks:raise MethodError('有効な出典付き回答が返りませんでした。')
    suggestion_html=''
    for widget in widgets:
        # Original provider widget is preserved inside a script-disabled, opaque-origin frame.
        child='<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src https: data:">'+widget
        suggestion_html+='<iframe title="Google検索の候補" sandbox="allow-popups allow-popups-to-escape-sandbox" srcdoc="'+escape(child,quote=True)+'"></iframe>'
    links=''.join(f'<li id="source{i}"><a href="{escape(url,quote=True)}" rel="noopener noreferrer">{escape(title)}</a></li>' for i,(url,title) in enumerate(sources,1))
    return '<!doctype html><html lang="ja"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; frame-src \'self\' about:; img-src https: data:"><title>トメリス・Google検索連携</title><style>body{font:17px/1.8 sans-serif;background:#edf5f8;color:#234;padding:32px;max-width:960px;margin:auto}.answer{white-space:pre-wrap;background:white;padding:24px;margin:20px 0}a{color:#126480}iframe{border:0;width:100%;height:200px;background:white}</style><h1>Google検索連携の回答</h1><p>質問：'+escape(question)+'</p><p>GoogleのAIが作成した回答です。引用先の内容・結論の正確さをトメリスが検証したものではありません。</p>'+''.join(blocks)+'<h2>出典</h2><ol>'+links+'</ol>'+suggestion_html+'</html>'

def save_grounding(data,question,directory):
    html=render_grounding(data,question)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',prefix='google_',suffix='.html',dir=directory,delete=False) as file:file.write(html);return Path(file.name)
