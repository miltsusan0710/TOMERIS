"""User-selected ZIP backup of local memory and planning data only."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import zipfile
from tomeris_weekly import DesktopService as WeeklyService

from tomeris_catalogue_schema import validate_catalogue,MAX_SOURCE_BYTES
FILES=('tomeris_memory.json','daily_plans.json','plan_progress.json','plan_reflections.json','research_sources.json','research_history.json')
from tomeris_research_journal import validate as validate_journal, MAX_BYTES as MAX_JOURNAL_BYTES
MAX_FILE_BYTES=32*1024*1024

class DesktopService(WeeklyService):
    def export_backup(self,destination):
        destination=Path(destination).absolute()
        if destination.suffix.lower()!='.zip':
            raise ValueError('保存ファイル名の末尾を .zip にしてください。')
        if destination.exists():
            raise ValueError('同じ名前のファイルがあります。別の名前で保存してください。')
        payload={}; missing=[]
        for name in FILES:
            source=self.data_dir/name
            if not source.exists():
                if name=='tomeris_memory.json':
                    raise ValueError('記憶ファイルが見つからないため、バックアップを作成できません。')
                missing.append(name); continue
            if source.is_symlink() or source.resolve().parent!=self.data_dir.resolve():
                raise ValueError('保存データの参照先が通常と異なります。バックアップを中止しました。')
            limit=MAX_SOURCE_BYTES if name=='research_sources.json' else (MAX_JOURNAL_BYTES if name=='research_history.json' else MAX_FILE_BYTES)
            with source.open('rb') as handle:
                raw=handle.read(limit+1)
            if len(raw)>limit:
                raise ValueError(f'{name} が大きすぎます。手動でのバックアップが必要です。')
            try:
                data=json.loads(raw)
                if not isinstance(data,dict): raise ValueError()
            except (ValueError,UnicodeError):
                raise ValueError(f'{name} をJSONとして読み取れません。元のファイルは変更していません。') from None
            if name=='research_sources.json':validate_catalogue(data)
            if name=='research_history.json':validate_journal(data)
            payload[name]=raw
        manifest={'format':'tomeris-data-backup','version':1,'app_version':'0.43',
                  'created_at':datetime.now(timezone(timedelta(hours=9))).isoformat(),
                  'files':[{'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in payload.items()],
                  'not_created':missing,'excluded':['Google connection information','application code','Ollama models','persona file','external knowledge files']}
        readme=('トメリスの記憶・計画データのバックアップです。\n'
                '会話・長期記憶・比較記録はtomeris_memory.jsonに含まれます。\n'
                '作成済みの場合のみ、計画・完了状態・振り返り・調査履歴・保存した調査資料と資料学習の有効／停止設定も含まれます。\n'
                'Google認証情報、アプリ本体、Ollamaモデル、人格ファイル、外部知識ファイルは含みません。\n'
                'このZIPは暗号化していません。個人の会話や記録が含まれるため、保管先を選んでください。\n'
                'manifest.jsonに各データのサイズとSHA-256を記録しています。\n'
                'v0.17以降の「データ」メニューから、内容を検査して別フォルダーに復元できます。\n')
        created=False
        try:
            with destination.open('xb') as handle:
                created=True
                with zipfile.ZipFile(handle,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                    for name,raw in payload.items(): archive.writestr(name,raw)
                    archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
                    archive.writestr('README.txt',readme.encode('utf-8'))
            with zipfile.ZipFile(destination) as archive:
                if archive.testzip() is not None: raise OSError('ZIPの整合性を確認できませんでした。')
                for name,raw in payload.items():
                    if archive.read(name)!=raw: raise OSError('バックアップの内容が元のデータと一致しません。')
        except Exception:
            if created:
                try: destination.unlink()
                except OSError: pass
            raise
        return (f'バックアップを保存し、内容の一致を確認しました。\n{destination}\n\n'
                f'保存データ：{len(payload)}ファイル（記憶・作成済みの計画・調査資料）。\n'
                'Google接続情報・アプリ本体・モデル・人格／外部知識ファイルは含みません。\n'
                'ZIPは暗号化されていません。個人の記録として保管してください。')
