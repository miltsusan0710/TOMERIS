"""Carry an unresolved public-person name into the immediately supplied URL."""
import re
from tomeris_person_profile import DesktopService as BaseService
from tomeris_web_search import public_url


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_profile_url = None

    def clear_tool_context(self):
        self.pending_profile_url = None
        return super().clear_tool_context()

    def report(self, question, progress=None, model=None):
        target = self.profile_request
        self.pending_profile_url = None
        answer = super().report(question, progress, model)
        if target and not self.demo and self.methods.mode == '自動' and not self.last_evidence_items:
            self.pending_profile_url = target[0]
        return answer

    def prepare_context(self, text):
        pending = self.pending_profile_url
        self.pending_profile_url = None
        url = text.strip()
        if pending and re.fullmatch(r'https?://\S+', url):
            if not public_url(url) or len(url) > 2500:
                return text, self.track(text, '公開プロフィールのHTTP/HTTPS URLを入力してください。このURLは取得していません。')
            self.clear_tool_context()
            # Keep the name as the subject; do not revert to an unfiltered
            # generic URL preview. The page reader applies DNS/redirect checks.
            answer = self.report(pending+' '+url)
            return text, answer+'\n指定ページを本人の公式資料と認定したわけではありません。'
        return super().prepare_context(text)
