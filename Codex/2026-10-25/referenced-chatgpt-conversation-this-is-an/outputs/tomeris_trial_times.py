"""Validate recorded acquisition/review chronology without claiming source freshness."""
from datetime import datetime

def timestamp(value,label):
    if not isinstance(value,str):raise ValueError(label+'がありません。再取得・再採点してください。')
    try:result=datetime.fromisoformat(value)
    except ValueError:raise ValueError(label+'の形式が不正です。') from None
    if result.utcoffset() is None:raise ValueError(label+'にタイムゾーンが必要です。')
    return result

def validate_times(record,review):
    finished=timestamp(record.get('finished_at'),'取得完了日時')
    reviewed=timestamp(review.get('reviewed_at'),'採点日時')
    if reviewed<finished:raise ValueError('採点日時が取得完了日時より前です。記録を確認してください。')
    started=timestamp(record['started_at'],'取得開始日時') if 'started_at' in record else None
    if started is not None and started>finished:raise ValueError('取得開始日時が完了日時より後です。')
    for page in record.get('pages',[]):
        # Older saved records may lack individual request times; never invent one.
        if not isinstance(page,dict):raise ValueError('取得資料の形式が不正です。')
        if 'checked_at' not in page:continue
        checked=timestamp(page['checked_at'],'資料の取得確認日時')
        if checked>finished or (started is not None and checked<started):raise ValueError('資料の取得確認日時が取得期間外です。')
