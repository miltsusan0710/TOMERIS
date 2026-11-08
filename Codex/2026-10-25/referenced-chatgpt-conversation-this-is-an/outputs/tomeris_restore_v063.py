"""Validate completion and reflection rows before writing a restored folder."""
import json
from tomeris_restore_v059 import DesktopService as BaseService, read_backup as base_read_backup


def validate_rows(document, reflection=False):
    if not isinstance(document, dict) or document.get('version') != 1 or not isinstance(document.get('plans'), dict):
        raise ValueError('計画関連データの形式が不正です。')
    for value in document['plans'].values():
        if reflection:
            if not isinstance(value, list) or not value:
                raise ValueError('振り返り記録の一覧形式が不正です。')
            for row in value:
                if not isinstance(row, dict) or not isinstance(row.get('text'), str) or not 1 <= len(row['text'].strip()) <= 2000:
                    raise ValueError('振り返り記録の本文が不正です。')
        elif (not isinstance(value, dict) or not isinstance(value.get('done'), list)
              or not 1 <= len(value['done']) <= 3 or any(type(flag) is not bool for flag in value['done'])):
            raise ValueError('完了記録のチェック状態が不正です。')


def read_backup(path):
    checked = base_read_backup(path)
    for name, reflection in (('plan_progress.json', False), ('plan_reflections.json', True)):
        if name in checked['payload']:
            validate_rows(json.loads(checked['payload'][name]), reflection)
    return checked


class DesktopService(BaseService):
    def export_backup(self, destination):
        self._progress()
        self._reflections()
        return BaseService.export_backup(self, destination)

    def inspect_backup(self, path):
        checked = read_backup(path)
        return {key:value for key,value in checked.items() if key != 'payload'} | {'files':list(checked['payload'])}

    def restore_backup(self, path, parent, expected_digest):
        checked = read_backup(path)
        if checked['digest'] != expected_digest:
            raise ValueError('確認後にZIPが変わりました。もう一度選び直してください。')
        return BaseService.restore_backup(self, path, parent, expected_digest)
