import sys,threading
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,urlencode
from urllib.request import build_opener, ProxyHandler
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tomeris_google as g
threads=[]; problems=[]
def fake_browser(url):
    query=parse_qs(urlsplit(url).query)
    redirect=query['redirect_uri'][0]
    assert urlsplit(redirect).hostname=='127.0.0.1'
    assert query['code_challenge_method']==['S256']
    def callback():
        try:
            with build_opener(ProxyHandler({})).open(redirect+'?'+urlencode({'state':query['state'][0],'code':'fake-code'}),timeout=5) as response:
                assert response.status==200
        except Exception as exc:
            problems.append(type(exc).__name__); print(type(exc).__name__, str(exc))
    thread=threading.Thread(target=callback); threads.append(thread); thread.start()
    return True
with patch.object(g.webbrowser,'open',side_effect=fake_browser),patch.object(g,'request_json',return_value={'test':'ok'}) as exchange:
    result=g.authorize({'client_id':'test','client_secret':'fake'},threading.Event(),timeout=5)
    assert result=={'test':'ok'}
    form=exchange.call_args.kwargs['form']
    assert form['code']=='fake-code' and len(form['code_verifier'])>=43
for thread in threads:
    thread.join(6)
assert not problems,problems
cancel=threading.Event(); cancel.set()
with patch.object(g.webbrowser,'open',return_value=True):
    try:
        g.authorize({'client_id':'test','client_secret':'fake'},cancel,timeout=1)
    except g.GoogleError:
        pass
    else:
        raise AssertionError('cancel not honored')
print('Local OAuth callback, PKCE exchange and cancellation: OK (no real Google login)')


