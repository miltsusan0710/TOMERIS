"""Match katakana middle-dot variants while preserving verbatim excerpts."""
import re
import unicodedata
from tomeris_person_url import DesktopService as BaseService
from tomeris_strict_evidence import terms, matches
from tomeris_prose_evidence import URL, UI, PROSE


def comparable(text):
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'(?<=[ァ-ヶー])・(?=[ァ-ヶー])', '', text)


def passages(page, topic):
    anchors = terms(comparable(topic))
    if not anchors:
        return []
    chosen = []
    for line in page['text'].splitlines():
        if UI.search(line):
            continue
        for sentence in re.split(r'(?<=[。！？])\s*|(?<=[.!?])\s+', line):
            sentence = sentence.strip()
            prose = URL.sub('', sentence).strip()
            if not 20 <= len(sentence) <= 350 or len(prose) < 20:
                continue
            if not PROSE.search(prose) or not matches(comparable(prose), anchors):
                continue
            if sentence not in chosen:
                chosen.append(sentence)
            if len(chosen) == 2:
                return chosen
    return chosen


class DesktopService(BaseService):
    extract_passages = staticmethod(passages)
