"""Normalize information requests before any generative conversation fallback."""
import re
from tomeris_auto_research_v029 import instruction

# Personal requests stay local. This is a bounded parser, not an LLM truth judge.
PERSONAL = re.compile(r'^(?:私|わたし|僕|ぼく|自分|あなた|トメリス)(?:の|は|$)|^(?:今日の予定|保存された記憶|会話履歴)$')
ABOUT = re.compile(r'(.{1,120}?)(?:について|に関して)(?:もっと|詳しく)?(?:知りたい|教えて|説明して|調べて|教えてほしい|知りたいです)(?:ください|です)?[。！？!?]*')
DEFINE = re.compile(r'(.{1,80}?)(?:とは|って何|ってなに)(?:何|なに)?(?:ですか|なの)?[。！？!?]*')
ATTRIBUTE = re.compile(r'(.{1,80}?)の(学費|入試|偏差値|所在地|住所|創業者|設立年|発売日|料金|価格|社長|学長)(?:は|を)?(?:知りたい|教えて|教えてください|誰|だれ|いくら|どこ|いつ)?(?:ですか)?[。！？!?]*')

def research_intent(text):
    method, phrase = instruction(text)
    phrase = phrase.strip()
    if re.search(r'検索しない|検索せず|調べない|ネットを使わ', phrase):
        return None
    attribute = ATTRIBUTE.fullmatch(phrase)
    match = ABOUT.fullmatch(phrase) or DEFINE.fullmatch(phrase) or attribute
    if not match:
        return None
    subject = match[1].strip()
    if PERSONAL.search(subject) or re.search(r'[\n「」『』]|https?://', subject):
        return None
    if subject in ('それ','これ','あれ','そのこと'):
        return dict(subject=None, query=None, method=method)
    query = subject+' '+attribute[2]+' 現在 公式' if attribute else subject+'について調べて'
    if method:
        query = text.replace(phrase, query, 1)
    return dict(subject=subject, query=query, method=method)
