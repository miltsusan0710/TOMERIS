"""Reject memory tag lists that crash the existing context builder."""
import json
from tomeris_restore_v058 import DesktopService as BaseService, read_backup as base_read_backup
from tomeris_backup_v050 import MAX_FILE_BYTES


def validate_memory_tags(document):
    # Missing fields, ignored legacy rows and non-list tags remain supported
    # by the current memory reader. Only reject a demonstrated crash shape.
    if not isinstance(document, dict):
        raise ValueError('記憶ファイルの形式を確認してください。')
    rows = document.get('memories', [])
    if not isinstance(rows, list):
        raise ValueError('長期記憶の一覧形式を確認してください。')
    for row in rows:
        if not isinstance(row, dict):
            continue
        tags = row.get('tags')
        if isinstance(tags, list) and any(not isinstance(tag, str) for tag in tags):
            raise ValueError('長期記憶のタグ一覧に文字列以外が含まれています。元データは変更していません。')


def read_backup(path):
    checked = base_read_backup(path)
    validate_memory_tags(json.loads(checked['payload']['tomeris_memory.json']))
    return checked


class DesktopService(BaseService):
    def export_backup(self, destination):
        with (self.data_dir/'tomeris_memory.json').open('rb') as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError('記憶ファイルが大きすぎます。')
        validate_memory_tags(json.loads(raw))
        return BaseService.export_backup(self, destination)

    def inspect_backup(self, path):
        checked = read_backup(path)
        return {key:value for key,value in checked.items() if key != 'payload'} | {'files':list(checked['payload'])}

    def restore_backup(self, path, parent, expected_digest):
        checked = read_backup(path)
        if checked['digest'] != expected_digest:
            raise ValueError('確認後にZIPが変わりました。もう一度選び直してください。')
        return BaseService.restore_backup(self, path, parent, expected_digest)
