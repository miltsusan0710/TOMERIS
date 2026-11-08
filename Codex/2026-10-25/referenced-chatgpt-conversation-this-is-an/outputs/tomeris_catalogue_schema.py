"""Offline schema checks for source catalogues, including untrusted ZIP input."""
from datetime import datetime
from urllib.parse import urlsplit
import ipaddress
MAX_SOURCE_BYTES=1000000

def validate_catalogue(document):
    def reject():raise ValueError('保存資料の形式・URL・取得日時を確認できません。')
    if not isinstance(document,dict) or type(document.get('version')) is not int or document['version']!=1 or type(document.get('enabled')) is not bool:reject()
    rows=document.get('rows')
    if not isinstance(rows,list) or len(rows)>200:reject()
    seen=set()
    for row in rows:
        if not isinstance(row,dict):reject()
        for key,limit in (('url',3000),('title',300),('excerpt',1200),('retrieved',80)):
            if not isinstance(row.get(key),str) or len(row[key])>limit:reject()
        url=row['url']
        if url in seen or any(ord(c)<32 or c.isspace() for c in url):reject()
        seen.add(url)
        try:
            p=urlsplit(url);host=p.hostname or ''
            if p.scheme not in ('http','https') or p.username is not None or p.password is not None or p.port not in (None,80,443) or '.' not in host or host.lower().rstrip('.').endswith(('.local','.localhost','.internal')):reject()
            try:address=ipaddress.ip_address(host)
            except ValueError:address=None
            if address is not None and not address.is_global:reject()
            moment=datetime.fromisoformat(row['retrieved'].replace('Z','+00:00'))
            if moment.tzinfo is None or moment.utcoffset() is None:reject()
        except (ValueError,TypeError):reject()
    return len(rows)
