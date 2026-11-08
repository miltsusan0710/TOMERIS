"""Offline paired evaluation of source reuse, using labelled fixtures, not AI grading.
No production data or network. Output timings are local test overhead only.
"""
import json,time,tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from tomeris_desktop_v037 import DesktopService
from tomeris_page_reader import PageError

GOOD='https://example.com/ollama'
OTHER='https://example.net/unrelated'
ROW=dict(title='Ollamaの説明',url=GOOD,snippet='Ollamaの機能についての説明。',wiki_id=1,wiki_lang='ja')
PAGE=dict(title='Ollamaの説明',url=GOOD,text='Ollamaはローカル環境でモデルを動かすためのツールとして説明されています。',published='')
SEED=dict(url=GOOD,title='Ollamaの説明',excerpt='Ollamaの保存時だけの記録：CACHE_ONLY_SENTINEL',retrieved='2026-10-29T00:00:00+09:00')
SCENARIOS=[
 dict(name='検索が正常',query='Ollamaについて調べて',rows=[ROW],seed=[SEED],pages={GOOD:PAGE},expected=(1,1)),
 dict(name='検索候補が空・既知の出典は取得可能',query='Ollamaについて調べて',rows=[],seed=[SEED],pages={GOOD:PAGE},expected=(0,1)),
 dict(name='無関係な候補・既知の出典は取得可能',query='Ollamaについて調べて',rows=[dict(title='別の製品',url=OTHER,snippet='別の製品')],seed=[SEED],pages={OTHER:dict(PAGE,url=OTHER,title='別の製品',text='対象とは異なる製品について説明するページの本文です。'),GOOD:PAGE},expected=(0,1)),
 dict(name='保存出典も取得失敗',query='Ollamaについて調べて',rows=[],seed=[SEED],pages={},expected=(0,0)),
 dict(name='無関係な保存資料',query='Ollamaについて調べて',rows=[],seed=[dict(SEED,title='別の製品',excerpt='別の製品の保存時の情報')],pages={GOOD:PAGE},expected=(0,0)),
 dict(name='最新情報に保存資料を使わない',query='今のOllamaニュースを調べて',rows=[],seed=[SEED],pages={GOOD:PAGE},expected=(0,0)),
 dict(name='同じ出典の重複',query='Ollamaについて調べて',rows=[ROW,dict(ROW)],seed=[SEED],pages={GOOD:PAGE},expected=(1,1)),
 dict(name='明示したWikipedia指定を保持',query='WikipediaでOllamaについて調べて',rows=[],seed=[SEED],pages={GOOD:PAGE},expected=(0,0)),
]

def trial(case,enabled,root):
    with tempfile.TemporaryDirectory(dir=root) as folder:
        service=DesktopService(Path(folder),demo=True);service.demo=False
        calls=[];success=[]
        def fetch(url):
            calls.append(url)
            if url not in case['pages']:raise PageError('評価用の取得失敗')
            success.append(url);return dict(case['pages'][url])
        try:
            service.catalogue.save(case['seed'],enabled)
            started=time.perf_counter()
            with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('evaluation must be offline')),patch('tomeris_search_methods.wikipedia_search',return_value=case['rows']),patch('tomeris_search_methods.search_web',return_value=[]),patch('tomeris_research_learning.search_web',return_value=[]),patch('tomeris_evidence_v029.fetch_page',side_effect=fetch),patch('tomeris_evidence_v029.wikipedia_page',side_effect=lambda row:fetch(row['url'])):
                answer=service.web_chat(case['query'],'not-used',automatic=True)
            elapsed=round((time.perf_counter()-started)*1000,3)
            displayed=[item['page']['url'] for item in service.last_evidence_items]
            assert 'CACHE_ONLY_SENTINEL' not in answer, 'saved text leaked into new evidence'
            assert set(displayed)<={GOOD}, 'unrelated source was displayed'
            assert len(displayed)==len(set(displayed)), 'duplicate source was displayed'
            assert len(displayed)==case['expected'][int(enabled)],(case['name'],enabled,displayed)
            return dict(enabled=enabled,page_requests=len(calls),successful_fetches=len(success),relevant_sources=len(displayed),unique_sources=len(set(displayed)),duplicate_sources=len(displayed)-len(set(displayed)),cached_text_reused=False,elapsed_ms=elapsed,requested_urls=calls,displayed_urls=displayed)
        finally:service.close()

def evaluate(root):
    return [dict(scenario=c['name'],question=c['query'],without_learning=trial(c,False,root),with_learning=trial(c,True,root)) for c in SCENARIOS]

def write_report(results,directory):
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'source_learning_evaluation.json').write_text(json.dumps(dict(version=1,mode='offline_labelled_fixtures',created_at=datetime.now(timezone.utc).isoformat(),cases=results),ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 資料学習の比較検証','', '同じ8つの質問・検索結果を、資料再利用なし／ありで比較しました。一時データと固定した模擬ページを使用し、ネットやAIの自己採点は使っていません。','', '|条件|根拠を表示できた件数（なし→あり）|本文取得の試行数（なし→あり）|', '|---|---:|---:|']
    for r in results:
        a,b=r['without_learning'],r['with_learning'];lines.append(f"|{r['scenario']}|{a['relevant_sources']} → {b['relevant_sources']}|{a['page_requests']} → {b['page_requests']}|")
    hits=[sum(r[key]['relevant_sources']>0 for r in results) for key in ('without_learning','with_learning')]
    requests=[sum(r[key]['page_requests'] for r in results) for key in ('without_learning','with_learning')]
    lines+=['',f'この固定シナリオでは、根拠を表示できた条件は{hits[0]}/8 → {hits[1]}/8でした。本文取得の試行は合計{requests[0]} → {requests[1]}回です。','', '## 確認したこと','', '- 検索候補が欠けても、関連する出典を保存していれば再取得で補える場合があります。','- 取得に失敗した出典の保存文を、今回の根拠として使い回しません。','- 無関係な保存資料・最新情報の質問・指定した検索方法に反する資料は追加しません。','- 表示した重複出典は全条件で0件でした。','', '## 限界','', 'この結果は模擬ページを使った機能検証です。実際のWebでの正答率、検索品質、アクセス成功率、速度向上、モデル能力の成長を証明するものではありません。ページ内容が事実かどうかの評価も行っていません。','資料再利用によりアクセス回数が増える場合があります。JSONに記録した実行時間はローカル試験処理の時間であり、実際のネット応答時間ではありません。学習ありの方が速いとは結論づけません。','', '## 再実行','', '作業フォルダーで `py -3 -B outputs/tomeris_evaluate_sources.py` を実行できます。本番データは読みません。結果はoutputs/source_learning_evaluation.mdとJSONへ保存します。']
    (directory/'source_learning_evaluation.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    root=Path(__file__).resolve().parent.parent/'work'/'v07';root.mkdir(parents=True,exist_ok=True)
    results=evaluate(root);write_report(results,Path(__file__).resolve().parent)
    print('8 paired offline scenarios passed. Reports written. No real-world performance claim.')
