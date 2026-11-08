"""Refresh selected status even when a check raises an unexpected error."""
from tomeris_sources_ui import SourcesPanel as BasePanel


class SourcesPanel(BasePanel):
    def check_selected(self):
        row = self.selected()
        if not row:
            return

        def operation():
            try:
                return self.app.service.check_source(row['url'], row['revision'])
            except Exception:
                return '再取得失敗：確認処理を完了できませんでした。一覧を再読込してください。保存本文と取得日時は更新していません。'

        def checked(status):
            row['check'] = status
            self.show_selected()
            self.message.set('再取得の結果を詳細欄に表示しました。')

        self.run(operation, checked)
