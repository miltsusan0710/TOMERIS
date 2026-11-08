"""Validated user-selected public topics, independent of conversation history."""
import json,os,tempfile
from pathlib import Path
MAX_TOPIC_BYTES=4096
DEFAULT_TOPICS=['論理的思考','認知バイアス','情報リテラシー']

def validate_topics(data):
    if not isinstance(data,dict) or set(data)!={'version','topics'} or type(data['version']) is not int or data['version']!=1:
        raise ValueError('収集テーマの形式が不正です。')
    topics=data['topics']
    if not isinstance(topics,list) or not 1<=len(topics)<=3:raise ValueError('テーマは1〜3件で指定してください。')
    seen=set()
    for topic in topics:
        if not isinstance(topic,str) or not 1<=len(topic)<=80 or topic!=topic.strip() or any(ord(c)<32 for c in topic):raise ValueError('各テーマは改行のない1〜80文字で指定してください。')
        if '://' in topic or topic.lower().startswith('www.'):raise ValueError('URLではなく公開記事の対象名を指定してください。')
        key=topic.casefold()
        if key in seen:raise ValueError('同じテーマを重複させないでください。')
        seen.add(key)
    return data

class TopicSettings:
    def __init__(self,directory):self.path=Path(directory)/'auto_topics.json'
    def load(self):
        if not self.path.exists():return list(DEFAULT_TOPICS)
        with self.path.open('rb') as f:raw=f.read(MAX_TOPIC_BYTES+1)
        if len(raw)>MAX_TOPIC_BYTES:raise ValueError('テーマ設定が容量上限を超えています。')
        return list(validate_topics(json.loads(raw))['topics'])
    def save(self,topics):
        # Read existing first: never silently overwrite malformed settings.
        self.load()
        raw=json.dumps(validate_topics(dict(version=1,topics=topics)),ensure_ascii=False).encode('utf-8')
        if len(raw)>MAX_TOPIC_BYTES:raise ValueError('テーマ設定が容量上限を超えています。')
        fd,name=tempfile.mkstemp(prefix='auto_topics_',suffix='.tmp',dir=self.path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)
