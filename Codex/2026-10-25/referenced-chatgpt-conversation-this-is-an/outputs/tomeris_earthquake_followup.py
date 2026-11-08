"""Follow one JMA EventID without substituting another earthquake."""
from datetime import datetime
import re
from tomeris_earthquake import read_xml,dt,value,FEED,PAGE,JST,EarthquakeError,recent_earthquake
from tomeris_source_management import DesktopService as BaseService

TITLES={'震度速報','震源に関する情報','震源・震度に関する情報','震源・震度情報'}
def snapshot(previous=None,now=None):
    now=now or datetime.now(JST)
    root=read_xml(FEED)
    if not -120<=(now-dt(value(root,'updated'))).total_seconds()<=600:raise EarthquakeError('配信一覧の更新時刻を確認できません。')
    entries=[]
    for entry in root.findall('{*}entry'):
        link=entry.find('{*}link')
        if value(entry,'title') in TITLES and link is not None:entries.append((dt(value(entry,'updated')),link.get('href','')))
    seen=set()
    for _,url in sorted(entries,reverse=True)[:6]:
        if url in seen:continue
        seen.add(url);report=read_xml(url)
        event=value(report,'Head/EventID')
        if not re.fullmatch(r'[0-9]{14}',event):raise EarthquakeError('地震の識別番号を確認できません。')
        if previous and event!=previous['event_id']:continue
        if value(report,'Control/Status')!='通常':raise EarthquakeError('対象の電文は訓練・試験などのため使用しません。')
        published=dt(value(report,'Head/ReportDateTime'));kind=value(report,'Head/InfoType')
        if not -120<=(now-published).total_seconds()<=900:raise EarthquakeError('対象地震の直近15分の発表を確認できません。')
        if previous and published<previous['published']:raise EarthquakeError('前回より古い電文が返りました。以前の震源に戻しません。')
        if kind not in ('発表','訂正','取消'):raise EarthquakeError('電文の発表種別を確認できません。')
        record=dict(event_id=event,published=published,kind=kind,title=value(report,'Control/Title'),url=url,checked=now,place='',occurred=None)
        if kind=='取消':return record
        occurred=dt(value(report,'Body/Earthquake/OriginTime') or value(report,'Head/TargetDateTime'))
        if not -120<=(now-occurred).total_seconds()<=900:raise EarthquakeError('対象時刻を直近15分の地震と確認できません。')
        record.update(occurred=occurred,place=value(report,'Body/Earthquake/Hypocenter/Area/Name'))
        if previous and previous['kind']=='取消' and published<=previous['published']:raise EarthquakeError('取消後の新しい発表を確認できません。')
        return record
    raise EarthquakeError('対象地震の後続発表は確認できませんでした。別の地震の発表で代用しません。' if previous else '取得した一覧に地震情報がありません。地震がなかったという意味ではありません。')

def render(record,previous=None):
    lines=['気象庁の発表：'+record['title'],'地震の識別番号：'+record['event_id'],'発表時刻：'+record['published'].astimezone(JST).strftime('%Y-%m-%d %H:%M:%S JST')]
    if previous:lines.insert(0,'前回と同じ地震の発表を確認しました。')
    if record['kind']=='取消':lines.append('この電文は取消です。以前の震源情報を有効な情報として再表示しません。')
    else:
        lines.append('対象時刻：'+record['occurred'].astimezone(JST).strftime('%Y-%m-%d %H:%M:%S JST'))
        if record['kind']=='訂正':lines.append('訂正された発表です。')
        lines.append('震源地：'+record['place'] if record['place'] else '震源地：この発表では未確認です。')
        if previous and record['published']==previous['published'] and record['url']==previous['url']:lines.append('新しい発表は取得していません。同じ電文です。')
    lines.extend(['あなたが感じた揺れとの一致や、津波・避難の要否はこの表示では判断できません。',PAGE,'出典電文：'+record['url'],'取得：'+record['checked'].astimezone(JST).strftime('%Y-%m-%d %H:%M:%S JST')])
    return '\n'.join(lines)

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.earthquake_record=None
    def special(self,text):
        compact=text.strip().rstrip('？?。！!')
        explicit_followup=compact in ('地震の続報は','さっきの地震の続報は','同じ地震の続報は')
        continuation=explicit_followup or (self.earthquake_record is not None and compact in ('その後は','続報は','震源は分かった','震源はわかった','もう一度確認して'))
        if continuation or recent_earthquake(text):
            previous=self.earthquake_record if continuation else None
            self.pending_weather=None;self.last_research_request=None
            if continuation and previous is None:return self.track(text,'この起動中に確認した地震がありません。まず「今の地震の震源は？」で発表を確認してください。')
            if self.demo:return self.track(text,'画面確認用：地震の発表は取得していません。')
            try:
                record=snapshot(previous);answer=render(record,previous);self.earthquake_record=record
            except EarthquakeError as exc:
                if not continuation:self.earthquake_record=None
                answer='地震の最新状況は未確認です。\n'+str(exc)+'\n保存した古い震源や別の地震では補っていません。\n'+PAGE
            return self.track(text,answer)
        self.earthquake_record=None
        return super().special(text)
