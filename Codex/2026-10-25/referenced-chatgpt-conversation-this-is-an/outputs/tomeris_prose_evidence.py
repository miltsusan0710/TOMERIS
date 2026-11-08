"""Conservative prose selection. This is a text filter, not fact verification."""
import re
from tomeris_strict_evidence import terms, matches
from tomeris_context_boundaries import DesktopService as BaseService

# Remove URLs only for qualification; quotes retain the original text exactly.
URL = re.compile(r'(?:https?://|www\.)[^\s<>]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}(?:/[^\s<>]*)?', re.I)
UI = re.compile(r'テンプレートを表示|ナビゲーションに移動|検索に移動|このページを編集|プライバシー・ポリシー|メインメニュー|toggle navigation', re.I)
PROSE = re.compile(r'[はがをにでとのもへ][ぁ-ゖァ-ヶ一-龥]|\b(?:is|are|was|were|can|provides|supports|allows|uses|runs)\b', re.I)

def passages(page, topic):
    anchors=terms(topic)
    if not anchors:return []
    chosen=[]
    for line in page['text'].splitlines():
        if UI.search(line):continue
        for sentence in re.split(r'(?<=[。！？])\s*|(?<=[.!?])\s+',line):
            sentence=sentence.strip()
            prose=URL.sub('',sentence).strip()
            if not 20<=len(sentence)<=350:continue
            if len(prose)<20 or not PROSE.search(prose):continue
            # A keyword appearing only inside a link does not establish relevance.
            if not matches(prose,anchors):continue
            if sentence not in chosen:chosen.append(sentence)
            if len(chosen)==2:return chosen
    return chosen

class DesktopService(BaseService):
    extract_passages=staticmethod(passages)
