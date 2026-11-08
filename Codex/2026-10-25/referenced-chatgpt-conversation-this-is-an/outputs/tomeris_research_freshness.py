"""Do not label a failed research attempt as a successful retrieval time."""
from tomeris_source_check_state import DesktopService as BaseService


class DesktopService(BaseService):
    def report(self, question, progress=None, model=None):
        answer = super().report(question, progress, model)
        if not getattr(self, 'last_evidence_items', []) and answer.startswith('調査対象：'):
            answer = answer.replace('\n取得日時：', '\n確認日時（本文根拠未取得）：', 1)
            # The failed report was tracked by the base service, not persisted.
            if self.session_turns and self.session_turns[-1][1] != answer:
                q, old = self.session_turns[-1]
                if old.replace('\n取得日時：', '\n確認日時（本文根拠未取得）：', 1) == answer:
                    self.session_turns[-1] = (q, answer)
        return answer
