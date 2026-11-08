"""Conservative natural-language shortcuts to existing, visible local controls.

This is bounded intent matching, not a general-purpose autonomous planner.
"""
import re
import unicodedata

PATTERNS = (
 ('today', r'(?:今日の)?(?:予定|スケジュール|計画)(?:を)?(?:見せて|表示して|開いて|確認したい)'),
 ('memories', r'(?:保存した|長期)?記憶(?:を)?(?:見せて|表示して|開いて|確認したい)'),
 ('sources', r'(?:学習した|保存した)?資料(?:を)?(?:見せて|表示して|開いて|確認したい)'),
 ('history', r'会話(?:の)?履歴(?:を)?(?:見せて|表示して|開いて|確認したい)'),
 ('pc', r'(?:パソコン|PC)(?:の)?情報(?:を)?(?:見せて|表示して|確認したい)'),
 ('image', r'(?:画像|写真)(?:を)?(?:見て|読み取って|確認したい)'),
 ('speak', r'(?:最後の|今の|さっきの)?(?:回答|返事)(?:を)?(?:読んで|読み上げて)'),
 ('settings', r'(?:会話)?設定(?:を)?(?:開いて|見せて|表示して)'),
)

def action_for(text):
    text=unicodedata.normalize('NFKC',text).strip()
    text=re.sub(r'^トメリス[、,\s]+','',text)
    text=re.sub(r'[。!！?？]+$','',text)
    for action,pattern in PATTERNS:
        if re.fullmatch(pattern,text,re.I):return action
    return None

def perform(app,action):
    if action in ('today','memories','history','pc'):app.view(action)
    elif action=='sources':app.open_sources()
    elif action=='settings':
        app.show_chat_settings.set(True);app.update_chat_layout()
    elif action=='speak' and not app.last_answer:app.append('お知らせ','読み上げる回答がまだありません。')
    elif action in ('image','speak'):app.media_actions[action]()
    else:raise ValueError('対応していない操作です。')
