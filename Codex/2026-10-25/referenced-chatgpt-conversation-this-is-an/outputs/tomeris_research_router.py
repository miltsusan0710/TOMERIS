"""Source requests never fall through to ungrounded conversation generation."""
import time
from tomeris_school_alias import DesktopService as BaseService
from tomeris_research_intent import research_intent
from tomeris_auto_research_v029 import instruction
from tomeris_overview import overview_subject, key
from tomeris_overview_resolution import ResolvedMethods
from tomeris_name_punctuation import passages
import re

class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods = ResolvedMethods(self.methods)

    def conversation_persona(self, text):
        style = super().conversation_persona(text)
        if re.search(r'この|その|新しい', text) and re.search(r'断定|おかげ|せい', text):
            style += ('\n原因については冒頭で「この説明だけでは原因を断定できません」と答える。'
                      '資料や実測データは渡されていない。「確認できます」「効果がある」は使わない。'
                      '変化はユーザーの報告であり未検証。比較する期間、作業量、他の変更点を尋ねる。')
        return style

    def extract_passages(self, page, topic):
        resolved = self.methods.resolved
        if (resolved and overview_subject(self.methods.question_context) == resolved['requested_title']
                and not getattr(self, '_detail_subject', None)
                and page.get('title') == resolved['title'] and page.get('provider','').startswith('Wikipedia')):
            lead = re.split(r'\n\s*==', page['text'], maxsplit=1)[0]
            # The article identity is already established by its exact title or
            # provider-declared redirect. Permit whitespace in the written name
            # (徳川 家康), but always return the untouched source sentence.
            sentences = re.split(r'(?<=[。！？])\s*|(?<=[.!?])\s+|\n+', lead)
            return [s.strip() for s in sentences if 20 <= len(s.strip()) <= 350
                    and key(resolved['title']) in key(s)][:2]
        # Overview evidence must describe the subject, not just mention it in
        # a book list or a related person's page. General detailed reports keep
        # the existing stricter per-topic extraction.
        return super().extract_passages(page, topic)

    def information_request(self, text, model=None, progress=None):
        intent = research_intent(text)
        if intent is None:
            return None
        if intent['subject'] is None:
            if self.flow_topic and time.monotonic()-self.flow_time <= 600:
                query = self.flow_topic+'について調べて'
                if intent['method']:
                    query = text.replace(instruction(text)[1], query, 1)
                return self.report(query, progress, model)
            return self.track(text, '何について知りたいですか？対象名を教えてください。')
        self.clear_tool_context()
        return self.report(intent['query'], progress, model)

    def chat(self, text, model, use_memory=False):
        answer = self.information_request(text, model)
        return answer if answer is not None else super().chat(text, model, use_memory)

    def web_chat(self, question, model, use_memory=False, automatic=False, progress=None):
        answer = self.information_request(question, model, progress)
        return answer if answer is not None else super().web_chat(question, model, use_memory, automatic, progress)

    def report(self, question, progress=None, model=None):
        intent = research_intent(question)
        if intent and intent['query']:
            question = intent['query']
        selected, phrase = instruction(question)
        subject = overview_subject(phrase)
        answer = super().report(question, progress, model)
        # Candidate availability alone is not success. Retry only automatic
        # overview retrieval, never a named provider or an unresolved subject.
        if (subject and not selected and self.methods.mode == '自動' and not self.demo
                and not self.last_evidence_items and not self.pending_subject
                and not getattr(self, '_continuing', False)):
            if progress:
                progress('本文根拠がないため一般Webでも確認します…')
            second = super().report(subject+' 公式', progress, model)
            self.flow_topic = subject
            self.flow_time = time.monotonic()
            if self.last_evidence_items:
                return '概要検索では本文根拠を取得できなかったため、一般Webで追加調査しました。\n\n'+second
            return second+'\n\n概要検索と一般Web検索の両方で本文根拠を確認できませんでした。未確認の内容を会話モデルで補っていません。'
        return answer
