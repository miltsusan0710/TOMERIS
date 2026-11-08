"""Explicit portable backup of comparison records and reviews; never restores in place."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from datetime import datetime,timezone
from tomeris_trial_export import child

MAX_TOTAL=64000000

def backup(directory,target):
    root=Path(directory).resolve();target=Path(target).resolve()
    if not root.is_dir():raise ValueError('比較記録フォルダーがありません。')
    if root==target.parent or root in target.parents:raise ValueError('保存先は比較記録フォルダーの外を選んでください。')
    entries=[];blobs=[];size=0
    for path in sorted(root.glob('*.json')):
        if len(entries)>=10000:raise ValueError('記録は10000ファイル以内です。')
        if path.is_symlink():raise ValueError('リンクされた記録は保存しません。')
        path=child(root,path.name)
        with path.open('rb') as f:data=f.read(1000001)
        if len(data)>1000000:raise ValueError('1ファイルは1MB以内です。')
        size+=len(data)
        if size>MAX_TOTAL:raise ValueError('合計64MB以内です。')
        entries.append(dict(name=path.name,size=len(data),sha256=hashlib.sha256(data).hexdigest()));blobs.append(data)
    manifest=dict(version=1,created_at=datetime.now(timezone.utc).isoformat(),files=entries,
        scope='比較試行と採点のJSON。記憶・計画・実験データセットは含みません。内容の正しさや採点の真偽は認定しません。')
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
        for entry,data in zip(entries,blobs):archive.writestr('records/'+entry['name'],data)
    # Build completely before exclusive creation. Existing files are never replaced.
    with target.open('xb') as f:f.write(buffer.getvalue())
    return manifest

def inspect(path):
    if Path(path).stat().st_size>MAX_TOTAL+10000000:raise ValueError('バックアップが大きすぎます。')
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        if len(names)>10001 or len(set(names))!=len(names):raise ValueError('項目数または重複が不正です。')
        if sum(i.file_size for i in infos)>MAX_TOTAL+3000000:raise ValueError('展開後のサイズが大きすぎます。')
        info=archive.getinfo('manifest.json')
        if info.file_size>3000000:raise ValueError('一覧が大きすぎます。')
        manifest=json.loads(archive.read(info))
        if not isinstance(manifest,dict) or manifest.get('version')!=1 or not isinstance(manifest.get('files'),list):raise ValueError('一覧の形式が不正です。')
        expected={'manifest.json'}
        for entry in manifest['files']:
            name=entry['name']
            if not isinstance(name,str) or '/' in name or '\\' in name or ':' in name or not name.endswith('.json'):raise ValueError('ファイル名が不正です。')
            member='records/'+name
            if member in expected:raise ValueError('一覧が重複しています。')
            expected.add(member);item=archive.getinfo(member)
            if item.file_size>1000000 or item.file_size!=entry['size']:raise ValueError('サイズが一致しません。')
            if hashlib.sha256(archive.read(item)).hexdigest()!=entry['sha256']:raise ValueError('内容が一致しません。')
        if expected!=set(names):raise ValueError('一覧にないファイルがあります。')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    create=sub.add_parser('create');create.add_argument('directory');create.add_argument('output')
    check=sub.add_parser('inspect');check.add_argument('archive');args=parser.parse_args()
    result=backup(args.directory,args.output) if args.action=='create' else inspect(args.archive)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
