"""Portable learning-state backup, validated before fresh-directory restore."""
import hashlib,io,json,os,stat,tempfile,zipfile
from pathlib import Path
from datetime import datetime,timezone
from tomeris_learning_review import snapshot,fingerprint

LIMITS={'retrieval_experience.json':200000,'learning_review.json':12000000}
MAX_ARCHIVE=13000000

def validate(name,raw):
    value=json.loads(raw)
    if not isinstance(value,dict) or value.get('version')!=1:raise ValueError('データ形式が不正です。')
    if name=='retrieval_experience.json':
        rows=value.get('attempts')
        if not isinstance(rows,list) or len(rows)>500:raise ValueError('経験記録が不正です。')
        for row in rows:
            if not isinstance(row,dict) or row.get('action') not in ('exact','normalized') or type(row.get('success')) is not bool:raise ValueError('経験記録が不正です。')
            if 'outcome' in row and (row['outcome'] not in ('evidence','no_candidate','no_evidence','retrieval_error') or row['success']!=(row['outcome']=='evidence')):raise ValueError('経験の結果が矛盾しています。')
    else:
        rows=value.get('rows')
        if not isinstance(rows,dict) or len(rows)>100:raise ValueError('確認記録が不正です。')
        for ident,row in rows.items():
            if not isinstance(row,dict) or row.get('status') not in ('pending','approved','rejected'):raise ValueError('確認状態が不正です。')
            if fingerprint(snapshot(row['item']))!=ident:raise ValueError('確認対象の内容が一致しません。')
            if not isinstance(row.get('reasons'),list) or not all(isinstance(x,str) for x in row['reasons']):raise ValueError('保留理由が不正です。')
    return value

def create(directory,target):
    directory=Path(directory).resolve();target=Path(target)
    payload={}
    for name,limit in LIMITS.items():
        path=directory/name
        if not path.exists():continue
        if path.is_symlink() or path.resolve().parent!=directory:raise ValueError('リンクされた資料は保存しません。')
        with path.open('rb') as f:raw=f.read(limit+1)
        if len(raw)>limit:raise ValueError('データの容量上限です。')
        validate(name,raw);payload[name]=raw
    if not payload:raise ValueError('まだ取得経験・確認待ち資料がありません。')
    manifest=dict(format='tomeris-learning-state',version=1,created_at=datetime.now(timezone.utc).isoformat(),
                  files={name:dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in payload.items()})
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest))
        for name,raw in payload.items():archive.writestr(name,raw)
    blob=buffer.getvalue();inspect_bytes(blob)
    with target.open('xb') as f:f.write(blob)
    return '取得経験・資料の確認記録を保存しました。\n'+str(target)+'\n通常の記憶・計画は含みません。ZIPは暗号化していません。'

def inspect_bytes(blob):
    if len(blob)>MAX_ARCHIVE:raise ValueError('ZIPが大きすぎます。')
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            infos=archive.infolist();names=[i.filename for i in infos]
            if len(names)!=len(set(names)) or not set(names)<=set(LIMITS)|{'manifest.json'} or 'manifest.json' not in names:raise ValueError('ZIPの項目が不正です。')
            for info in infos:
                if info.is_dir() or stat.S_ISLNK(info.external_attr>>16) or info.file_size>LIMITS.get(info.filename,10000) or info.flag_bits&1:raise ValueError('ZIPの形式・容量が不正です。')
            manifest=json.loads(archive.read('manifest.json'))
            files=manifest['files']
            if manifest.get('format')!='tomeris-learning-state' or manifest.get('version')!=1 or not isinstance(files,dict) or not files or set(files)!=set(names)-{'manifest.json'}:raise ValueError('一覧が不正です。')
            payload={}
            for name,entry in files.items():
                raw=archive.read(name)
                if len(raw)!=entry['size'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('内容が検査情報と一致しません。')
                validate(name,raw);payload[name]=raw
    except (zipfile.BadZipFile,KeyError,TypeError,AttributeError,UnicodeError,NotImplementedError) as exc:
        raise ValueError('バックアップを検証できません。') from exc
    return dict(digest=hashlib.sha256(blob).hexdigest(),payload=payload,created_at=manifest.get('created_at','不明'))

def inspect(path):
    with Path(path).open('rb') as f:blob=f.read(MAX_ARCHIVE+1)
    return inspect_bytes(blob)

def restore(path,parent,digest):
    checked=inspect(path)
    if checked['digest']!=digest:raise ValueError('確認後にZIPが変わりました。選び直してください。')
    parent=Path(parent).resolve(strict=True)
    folder=Path(tempfile.mkdtemp(prefix='tomeris_learning_restored_',dir=parent))
    written=[]
    try:
        for name,raw in checked['payload'].items():
            target=folder/name
            with target.open('xb') as f:written.append(target);f.write(raw)
            if target.read_bytes()!=raw:raise OSError('復元内容が一致しません。')
    except Exception:
        for target in written:target.unlink(missing_ok=True)
        folder.rmdir();raise
    return '別フォルダーへ復元しました。現在使用中の資料や設定は変更していません。\n'+str(folder)
