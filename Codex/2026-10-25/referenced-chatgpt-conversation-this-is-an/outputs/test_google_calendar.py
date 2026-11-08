import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import patch, Mock
from datetime import datetime
import tomeris_google as g

def token(value='access'):
    return {'access_token':value,'refresh_token':'refresh-'+value,'expires_in':3600,'scope':' '.join(g.SCOPES)}

def account(email):
    return {'email':email,**g.normalize_token(token(email))}

class GoogleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.api=g.GoogleCalendar(self.tmp.name)
        self.data={'version':1,'client':{'client_id':'test.apps.googleusercontent.com','client_secret':'fake-client-secret'},
                   'accounts':{'a':account('a@example.test'),'b':account('b@example.test')}}
    def tearDown(self):
        self.tmp.cleanup()
    def test_dpapi_persistence_and_atomic_failure(self):
        self.api.vault.write(self.data)
        before=self.api.vault.path.read_bytes()
        self.assertNotIn(b'fake-client-secret',before)
        self.assertNotIn(b'refresh-',before)
        self.assertEqual(self.api.vault.read(),self.data)
        with patch.object(g.os,'replace',side_effect=OSError()),self.assertRaises(OSError):
            self.api.vault.write({'version':1,'client':None,'accounts':{}})
        self.assertEqual(self.api.vault.path.read_bytes(),before)
        self.assertEqual(list(Path(self.tmp.name).glob('*.tmp')),[])
    def test_corrupt_vault_preserved(self):
        self.api.vault.path.write_bytes(b'corrupt')
        with self.assertRaises(g.GoogleError):
            self.api.status()
        self.assertEqual(self.api.vault.path.read_bytes(),b'corrupt')
    def test_config_only_desktop_and_no_client_switch(self):
        path=Path(self.tmp.name)/'client.json'
        path.write_text(json.dumps({'web':self.data['client']}))
        with self.assertRaises(g.GoogleError):
            self.api.configure(path)
        path.write_text(json.dumps({'installed':self.data['client']}))
        self.assertTrue(self.api.configure(path)['configured'])
        self.api.vault.write(self.data)
        other={**self.data['client'],'client_id':'other.apps.googleusercontent.com'}
        path.write_text(json.dumps({'installed':other}))
        with self.assertRaises(g.GoogleError):
            self.api.configure(path)
        self.assertEqual(self.api.vault.read(),self.data)
    def test_pkce_and_readonly_scopes(self):
        p=g.auth_parameters('id','http://127.0.0.1:1/oauth2callback','state','dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')
        self.assertEqual(p['code_challenge'],'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM')
        self.assertEqual(p['code_challenge_method'],'S256')
        self.assertNotIn('gmail',p['scope'])
        self.assertTrue(all(s.endswith('.readonly') for s in g.SCOPES[2:]))
    def test_callback_rejects_csrf_duplicates_and_wrong_path(self):
        for path in ['/oauth2callback?state=bad&code=x','/other?state=ok&code=x','/oauth2callback?state=%E3%81%82&code=x',
                     '/oauth2callback?state=ok&state=bad&code=x','/oauth2callback?state=ok&code=a&code=b']:
            self.assertIsNone(g.parse_callback(path,'ok'))
        self.assertEqual(g.parse_callback('/oauth2callback?state=ok&code=secret','ok'),'secret')
        with self.assertRaises(g.GoogleError):
            g.parse_callback('/oauth2callback?state=ok&error=access_denied','ok')
    def test_no_external_destination_or_calendar_write(self):
        with self.assertRaises(g.GoogleError):
            g.request_json('https://example.test',token='secret')
        with self.assertRaises(g.GoogleError):
            g.request_json(g.CALENDAR+'calendars/primary/events',form={'summary':'x'})
        self.assertIsNone(g.NoRedirect().redirect_request(None,None,None,None,None,'https://example.test'))
    def test_scope_rejection_and_refresh_preservation(self):
        for scopes in ['openid email', ' '.join(g.SCOPES)+' https://www.googleapis.com/auth/calendar']:
            with self.assertRaises(g.GoogleError):
                g.normalize_token({**token(),'scope':scopes})
        updated=token('new'); del updated['refresh_token']
        self.assertEqual(g.normalize_token(updated,{'refresh_token':'old'})['refresh_token'],'old')
    def test_connect_accounts_separate_and_duplicate_replaces(self):
        self.api.vault.write(self.data)
        info={'sub':'a','email':'a@example.test','email_verified':True}
        with patch.object(g,'authorize',return_value=token('new')),patch.object(g,'request_json',return_value=info):
            status=self.api.connect()
        self.assertEqual(len(status['accounts']),2)
        stored=self.api.vault.read()
        self.assertEqual(stored['accounts']['b'],self.data['accounts']['b'])
        self.assertEqual(stored['accounts']['a']['access_token'],'new')
        with patch.object(g,'authorize',side_effect=g.GoogleError('cancelled')),self.assertRaises(g.GoogleError):
            self.api.connect()
        self.assertEqual(self.api.vault.read(),stored)
    def test_cancel_prevents_account_save(self):
        self.api.vault.write(self.data); self.api.cancel.set()
        with patch.object(g,'authorize',return_value=token()),patch.object(g,'request_json',return_value={'sub':'c','email':'c@test','email_verified':True}),self.assertRaises(g.GoogleError):
            self.api.connect()
        self.assertEqual(self.api.vault.read(),self.data)
    def test_forget_local_only(self):
        self.api.vault.write(self.data)
        with patch.object(g,'request_json') as request:
            self.api.forget('a')
            request.assert_not_called()
        self.assertEqual(list(self.api.vault.read()['accounts']),['b'])
    def test_refresh_only_requested_account_and_once_after_401(self):
        self.api.vault.write(self.data)
        with patch.object(g,'request_json',side_effect=[g.GoogleError('expired',401),token('renewed'),{'items':[]}]) as request:
            self.assertEqual(self.api._get(self.data,'a','users/me/calendarList',{}),{'items':[]})
            self.assertEqual(request.call_count,3)
        stored=self.api.vault.read()
        self.assertEqual(stored['accounts']['b']['access_token'],'b@example.test')
        self.assertEqual(stored['accounts']['a']['access_token'],'renewed')
    def test_pagination_and_repeat_guard(self):
        with patch.object(self.api,'_get',side_effect=[{'items':[1],'nextPageToken':'next'},{'items':[2]}]) as get:
            self.assertEqual(self.api._pages(self.data,'a','path',{}),[1,2])
            self.assertEqual(get.call_args.args[-1]['pageToken'],'next')
        with patch.object(self.api,'_get',return_value={'nextPageToken':'same'}),self.assertRaises(g.GoogleError):
            self.api._pages(self.data,'a','path',{})
    def test_agenda_jst_hidden_all_day_and_partial_failure(self):
        self.api.vault.write(self.data)
        requests=[]
        def pages(data,key,path,params):
            requests.append((key,path,params))
            if key=='b':
                raise g.GoogleError('account expired')
            if path=='users/me/calendarList':
                return [{'id':'normal','summary':'個人'}, {'id':'hidden','hidden':True}, {'id':'unchecked','selected':False}]
            return [{'start':{'date':'2026-10-25'},'end':{'date':'2026-10-26'},'summary':'終日の予定'},
                    {'start':{'dateTime':'2026-10-25T01:00:00Z'},'end':{'dateTime':'2026-10-25T02:00:00Z'},'summary':'ミーティング'},
                    {'status':'cancelled'}]
        with patch.object(self.api,'_pages',side_effect=pages):
            result=self.api.agenda(now=datetime(2026,10,25,12,tzinfo=g.JST))
        self.assertIn('10:00〜11:00',result)
        self.assertIn('終日',result)
        self.assertIn('a@example.test',result); self.assertIn('b@example.test',result)
        self.assertIn('account expired',result)
        self.assertEqual(requests[1][2]['timeMin'],'2026-10-25T00:00:00+09:00')
        self.assertEqual(requests[1][2]['timeMax'],'2026-10-26T00:00:00+09:00')
        self.assertEqual(requests[1][2]['singleEvents'],'true')
        self.assertEqual(len(requests),3)
        self.assertEqual(self.api.vault.read(),self.data)
    def test_selected_account_does_not_read_other(self):
        self.api.vault.write(self.data)
        with patch.object(self.api,'_pages',return_value=[]) as pages:
            self.api.agenda('b')
            self.assertEqual(pages.call_args.args[1],'b')
            self.assertEqual(pages.call_count,1)
    def test_empty_and_cancelled_fetch(self):
        self.assertIn('未登録',self.api.agenda())
        self.api.cancel.set()
        with self.assertRaises(g.GoogleError):
            self.api._pages(self.data,'a','path',{})

if __name__=='__main__':
    unittest.main()
