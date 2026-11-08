"""Validate a Tomeris ZIP and restore only approved data names into a new folder."""
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import tempfile
import zipfile
from tomeris_backup_v043 import DesktopService as BackupService, FILES, MAX_FILE_BYTES

from tomeris_catalogue_schema import validate_catalogue,MAX_SOURCE_BYTES

from tomeris_research_journal import validate as validate_journal, MAX_BYTES as MAX_JOURNAL_BYTES

MAX_ARCHIVE_BYTES=len(FILES)*MAX_FILE_BYTES+256*1024


def read_backup(path):
    with Path(path).open('rb') as handle:
        raw=handle.read(MAX_ARCHIVE_BYTES+1)
    if len(raw)>MAX_ARCHIVE_BYTES:
        raise ValueError('バックアップが大きすぎるため読み込めません。')
    digest=hashlib.sha256(raw).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries=archive.infolist(); names=[entry.filename for entry in entries]
            if len(entries)>len(FILES)+2 or len(set(names))!=len(names):
                raise ValueError('重複した項目、または想定外の項目数があります。')
            allowed=set(FILES)|{'manifest.json','README.txt'}
            if not set(names)<=allowed or 'manifest.json' not in names or 'tomeris_memory.json' not in names:
                raise ValueError('トメリスのデータ以外が含まれるか、必要なファイルがありません。')
            for entry in entries:
                limit=MAX_SOURCE_BYTES if entry.filename=='research_sources.json' else (MAX_JOURNAL_BYTES if entry.filename=='research_history.json' else (MAX_FILE_BYTES if entry.filename in FILES else 64*1024))
                if entry.is_dir() or stat.S_ISLNK(entry.external_attr>>16) or entry.file_size>limit or entry.flag_bits&1 or entry.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):
                    raise ValueError('対応できない形式または大きさの項目があります。')
            def bounded(name,limit):
                with archive.open(name) as handle:
                    value=handle.read(limit+1)
                if len(value)>limit: raise ValueError('展開後のサイズが上限を超えています。')
                return value
            manifest=json.loads(bounded('manifest.json',64*1024))
            if not isinstance(manifest,dict) or manifest.get('format')!='tomeris-data-backup' or manifest.get('version')!=1 or not isinstance(manifest.get('files'),list):
                raise ValueError('トメリスのバックアップ形式として認識できません。')
            metadata={}
            for item in manifest['files']:
                if not isinstance(item,dict): raise ValueError('ファイル情報が不正です。')
                name=item.get('name'); size=item.get('bytes'); checksum=item.get('sha256')
                if name not in FILES or name in metadata or type(size) is not int or not 0<=size<=MAX_FILE_BYTES or not isinstance(checksum,str) or not re.fullmatch('[0-9a-f]{64}',checksum):
                    raise ValueError('ファイル情報が不正です。')
                metadata[name]=item
            if set(metadata)!=(set(names)&set(FILES)):
                raise ValueError('ファイル一覧とZIPの内容が一致しません。')
            payload={}; counts={}
            for name,item in metadata.items():
                value=bounded(name,MAX_SOURCE_BYTES if name=='research_sources.json' else (MAX_JOURNAL_BYTES if name=='research_history.json' else MAX_FILE_BYTES))
                if len(value)!=item['bytes'] or hashlib.sha256(value).hexdigest()!=item['sha256']:
                    raise ValueError('保存時の検査情報と一致しません。破損または変更された可能性があります。')
                document=json.loads(value)
                if not isinstance(document,dict): raise ValueError('データの形式が不正です。')
                if name=='tomeris_memory.json':
                    if document.get('version')!=3: raise ValueError('この記憶データのバージョンには対応していません。')
                    for key in ['conversations','memories','growth_log','decisions']:
                        if not isinstance(document.get(key,[]),list): raise ValueError('記憶データの形式が不正です。')
                    counts['conversations']=len(document.get('conversations',[])); counts['memories']=len(document.get('memories',[]))
                elif name=='research_sources.json':
                    counts['research_sources']=validate_catalogue(document)
                    counts['source_learning_enabled']=document['enabled']
                elif name=='research_history.json':
                    validate_journal(document)
                    counts['research_history']=len(document['records'])
                elif name=='daily_plans.json':
                    if document.get('version')!=1 or not isinstance(document.get('plans'),list): raise ValueError('計画データの形式が不正です。')
                    counts['plans']=len(document['plans'])
                elif document.get('version')!=1 or not isinstance(document.get('plans'),dict):
                    raise ValueError('計画関連データの形式が不正です。')
                payload[name]=value
            if 'README.txt' in names: bounded('README.txt',64*1024)
    except (zipfile.BadZipFile,KeyError,UnicodeError,TypeError,NotImplementedError) as exc:
        raise ValueError('ZIPが破損しているか、対応できない形式です。') from None
    return {'digest':digest,'payload':payload,'created_at':str(manifest.get('created_at','不明')),'counts':counts}

class DesktopService(BackupService):
    def inspect_backup(self,path):
        checked=read_backup(path)
        return {key:value for key,value in checked.items() if key!='payload'} | {'files':list(checked['payload'])}
    def restore_backup(self,path,parent,expected_digest):
        checked=read_backup(path)
        if checked['digest']!=expected_digest:
            raise ValueError('確認後にZIPが変わりました。もう一度選び直してください。')
        parent=Path(parent).resolve(strict=True)
        if not parent.is_dir(): raise ValueError('復元先の親フォルダーを選んでください。')
        stamp=datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S')
        folder=Path(tempfile.mkdtemp(prefix='tomeris_restored_'+stamp+'_',dir=parent))
        written=[]
        try:
            for name,value in checked['payload'].items():
                target=folder/name
                with target.open('xb') as handle:
                    written.append(target); handle.write(value)
                if target.read_bytes()!=value: raise OSError('復元したデータが元の内容と一致しません。')
        except Exception:
            for target in written:
                try: target.unlink()
                except OSError: pass
            try: folder.rmdir()
            except OSError: pass
            raise
        return str(folder)
