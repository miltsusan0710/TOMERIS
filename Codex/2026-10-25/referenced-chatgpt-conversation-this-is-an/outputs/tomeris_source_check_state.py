"""Bind volatile fetch status to the exact saved source revision."""
from datetime import datetime, timezone, timedelta
from tomeris_ratio_followup import DesktopService as BaseService


class DesktopService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source_check_revisions = {}

    def source_records(self, query=''):
        result = super().source_records(query)
        for row in result['rows']:
            if self.source_check_revisions.get(row['url']) != row['revision']:
                row['check'] = 'この保存内容の再取得確認は未実施（過去の確認結果は引き継ぎません）'
                self.source_checks.pop(row['url'], None)
                self.source_check_revisions.pop(row['url'], None)
        return result

    def check_source(self, url, expected):
        stamp = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
        self.source_check_revisions[url] = expected
        self.source_checks[url] = stamp + ' 再取得は未完了。以前の成功結果は今回の確認結果として使いません。'
        try:
            self.selected_source(url, expected)
            result = super().check_source(url, expected)
        except Exception:
            # Preserve failure state even when the UI handles an unexpected
            # exception. Do not expose raw exception text or cached success.
            self.source_checks[url] = stamp + ' 再取得失敗：確認処理を完了できませんでした。保存本文・取得日時は更新していません。'
            raise
        if self.demo:
            self.source_checks[url] = stamp + ' ' + result
        return result

    def remove_source(self, url, expected):
        result = super().remove_source(url, expected)
        self.source_check_revisions.pop(url, None)
        return result
