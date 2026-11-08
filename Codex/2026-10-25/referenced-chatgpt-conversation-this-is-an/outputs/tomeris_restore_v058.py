"""Match plan-row validation to the live reader before backup or restore."""
import json
from tomeris_restore_v050 import DesktopService as BaseService, read_backup as base_read_backup
from tomeris_plans import validate


def validate_plan_rows(document):
    if not isinstance(document, dict) or document.get('version') != 1 or not isinstance(document.get('plans'), list):
        raise ValueError('計画ファイルの形式を確認してください。')
    for row in document['plans']:
        if not isinstance(row, dict) or not isinstance(row.get('date'), str):
            raise ValueError('計画の記録形式が不正です。')
        validate(row.get('goal'), row.get('budget'), row.get('tasks'))


def read_backup(path):
    result = base_read_backup(path)
    raw = result['payload'].get('daily_plans.json')
    if raw is not None:
        validate_plan_rows(json.loads(raw))
    return result


class DesktopService(BaseService):
    def export_backup(self, destination):
        # The existing reader applies the same constraints without modifying data.
        self._plans()
        return BaseService.export_backup(self, destination)

    def inspect_backup(self, path):
        checked = read_backup(path)
        return {key:value for key,value in checked.items() if key != 'payload'} | {'files':list(checked['payload'])}

    def restore_backup(self, path, parent, expected_digest):
        checked = read_backup(path)
        if checked['digest'] != expected_digest:
            raise ValueError('確認後にZIPが変わりました。もう一度選び直してください。')
        # The original routine rechecks the entire file and digest before writing.
        return BaseService.restore_backup(self, path, parent, expected_digest)
