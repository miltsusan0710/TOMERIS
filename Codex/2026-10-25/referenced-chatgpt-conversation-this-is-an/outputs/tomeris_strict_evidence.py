"""Conservative complete-subject matching; no Japanese bigram matching."""
import re
import unicodedata
from urllib.parse import urlsplit

ALIASES=(('アイアンマン','iron man'),('ジャービス','jarvis'),('マーベル','marvel'))
STOP={'内容','説明','特徴','機能','方法','公式','情報','報告','調査','収集','比較','要約','正確','最新','何','何ができるか'}

def normalize(text):return unicodedata.normalize('NFKC',text).casefold()

def terms(text):
    text=normalize(text)
    urls=re.findall(r'https?://[^\s<>「」]+',text)
    text=re.sub(r'https?://[^\s<>「」]+',' ',text)
    text=re.sub(r'について|に関する|調べて|教えて|ください|公式サイト|サイト|情報収集|出して|正確に|詳しく|報告して|何ができるか',' ',text)
    anchors=[]
    for group in ALIASES:
        if any(re.search(re.escape(alias),text) for alias in group):
            anchors.append(group)
            for alias in group:text=text.replace(alias,' ')
    tokens=re.findall(r'[ァ-ヶー]{2,}|[一-龥々]{2,}|[a-z][a-z0-9_-]+',text)
    anchors.extend((token,) for token in tokens if token not in STOP)
    # A URL alone gives no subject. Do not pretend its hostname proves relevance.
    return tuple(dict.fromkeys(anchors))

def contains(text,word):
    text=normalize(text)
    if re.fullmatch(r'[ァ-ヶー]+',word):pattern=r'(?<![ァ-ヶー])'+re.escape(word)+r'(?![ァ-ヶー])'
    elif re.search(r'[a-z]',word):pattern=r'(?<![a-z0-9_])'+re.escape(word)+r'(?![a-z0-9_])'
    else:pattern=re.escape(word)
    return re.search(pattern,text) is not None

def matches(text,anchors):
    return bool(anchors) and all(any(contains(text,alias) for alias in group) for group in anchors)

def passages(page,topic):
    anchors=terms(topic)
    if not anchors:return []
    chosen=[]
    # Each displayed passage itself must contain every subject anchor.
    for line in page['text'].splitlines():
        for sentence in re.split(r'(?<=[。！？])\s*|(?<=[.!?])\s+',line):
            sentence=sentence.strip()
            if not 20<=len(sentence)<=350 or not matches(sentence,anchors):continue
            if sentence not in chosen:chosen.append(sentence)
            if len(chosen)==2:return chosen
    return chosen

def relevance_score(text,anchors):
    return sum(any(contains(text,alias) for alias in group) for group in anchors)
