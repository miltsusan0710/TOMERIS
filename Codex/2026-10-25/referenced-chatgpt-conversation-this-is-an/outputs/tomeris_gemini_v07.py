"""Gemini REST adapter: current question only, explicit approval per call."""
import getpass
import json
import os
import re
import warnings
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from tomeris_provider import ProviderError

DEFAULT_MODEL = 'gemini-3.5-flash'
CLOUD_SYSTEM = ('あなたはトメリス。日本語で冷静かつ率直に回答し、ユーザーの思考力・判断力・行動力・精神的な回復力を支援します。'
                '中心原則は長期的な勝利。最終判断はユーザーに委ねます。PC操作やファイル参照の権限はありません。'
                '実行や完了を宣言しないでください。リスク分析は指定数を守り、各項目に影響・具体策・実行前の確認を含めてください。')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class GeminiProvider:
    cloud = True

    def __init__(self, model=DEFAULT_MODEL):
        if not re.fullmatch(r'gemini-[A-Za-z0-9._-]+', model):
            raise ProviderError('GeminiのモデルIDが不正です。')
        self.model = model
        self._key = os.environ.get('GEMINI_API_KEY', '').strip()

    def enter_key(self):
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            try:
                key = getpass.getpass('APIキー（非表示・この起動中のみ保持）> ').strip()
            except (getpass.GetPassWarning, EOFError, KeyboardInterrupt):
                print('キー入力を中止しました。通常のPowerShellで実行してください。')
                return False
        if not key or not key.isascii() or any(c.isspace() for c in key):
            print('キーが空、または形式が不正です。')
            return False
        self._key = key
        print('キーをこの起動中のみ保持しました。ファイルには保存しません。')
        return True

    def check(self):
        if not self._key:
            return False, 'APIキー未設定。/gemini-key で非表示入力できます。'
        return True, 'キー設定済み（API接続は未検証）。質問の送信時に確認します。'

    def generate(self, messages):
        if not self._key:
            raise ProviderError('APIキー未設定。/gemini-key を実行してください。')
        users = [m['content'] for m in messages if m.get('role') == 'user']
        if not users or not isinstance(users[-1], str):
            raise ProviderError('質問がありません。')
        payload = {'systemInstruction': {'parts': [{'text': CLOUD_SYSTEM}]},
                   'contents': [{'role': 'user', 'parts': [{'text': users[-1]}]}]}
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        if len(body) > 128 * 1024:
            raise ProviderError('質問が大きすぎます。短くしてください。')
        print('\n送信先: generativelanguage.googleapis.com / ' + self.model)
        print('送信本文全体（記憶・過去会話・人格ファイル・PC情報は含めません）:')
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print('API利用枠を消費します。料金はGoogle側の設定に従います。')
        try:
            approved = input('この内容をGoogleへ送信しますか？ (yes/no) > ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            approved = ''
        if approved != 'yes':
            raise ProviderError('送信をキャンセルしました。')
        request = Request('https://generativelanguage.googleapis.com/v1beta/models/' + self.model + ':generateContent',
                          data=body, headers={'Content-Type': 'application/json', 'x-goog-api-key': self._key}, method='POST')
        opener = build_opener(ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=120) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise ProviderError('Geminiの応答が大きすぎます。')
            result = json.loads(raw)
            candidate = result.get('candidates', [])[0]
            if candidate.get('finishReason') != 'STOP':
                raise ProviderError('回答が完了しませんでした。質問を短くするか内容を変えてください。')
            answer = ''.join(p['text'] for p in candidate.get('content', {}).get('parts', [])
                             if isinstance(p, dict) and isinstance(p.get('text'), str) and not p.get('thought')).strip()
            if not answer:
                raise ProviderError('回答が空、またはブロックされました。')
            return answer.replace(self._key, '[APIキー非表示]')
        except HTTPError as exc:
            code = exc.code
            exc.close()
            detail = {400: '質問形式・モデル設定を確認してください。', 401: 'APIキーを確認してください。',
                      403: 'APIキーの権限・利用条件を確認してください。', 404: 'モデルIDを確認してください。',
                      429: '利用上限です。Google側の利用枠・課金設定を確認してください。'}.get(code, '時間をおいて再度お試しください。')
            raise ProviderError(f'Gemini HTTP {code}: {detail}') from None
        except (URLError, OSError):
            raise ProviderError('Geminiに接続できません。ネット接続を確認してください。') from None
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise ProviderError('回答が空、ブロック済み、または応答形式が不正です。') from None
