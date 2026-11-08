"""Read-only trial coverage window. No new searches or training."""
from tomeris_trial_coverage import summarize

LABELS={'search_error':'検索エラー','no_candidates':'候補なし','retrieval_failed':'先頭資料の取得失敗',
        'no_matching_evidence':'本文・引用根拠不足','both_have_evidence':'両方式の本文・引用あり','invalid':'不正・読み取り不能'}

def render(report):
    lines=['保存済み比較試行の取得状況', '集計日時：'+report['created_at'],
           '保存記録を集計した時刻です。ネットから再取得した時刻ではありません。',
           '試行総数：'+str(report['total'])]
    lines.extend(label+'：'+str(report['counts'][key]) for key,label in LABELS.items())
    lines+=['',report['limitation'],'未採点の記録も含みます。学習・通常回答への適用は行いません。','', '各試行の確認結果']
    for row in report['records']:
        lines+=['',row['file'],LABELS[row['status']]]
        if row.get('finished_at'):lines+=['記録の取得日時：'+row['finished_at']]
        if row.get('error'):lines+=['理由：'+row['error']]
    return '\n'.join(lines)

def open_coverage(app):
    if app.busy or app.closing:return
    def work():
        try:outcome=(summarize(app.service.data_dir/'research_trials'),None)
        except (OSError,ValueError) as exc:outcome=(None,str(exc))
        return done,outcome
    def done(outcome):
        if app.closing:return
        from tkinter import Toplevel
        from tkinter.scrolledtext import ScrolledText
        report,error=outcome
        window=Toplevel(app.root);window.title('比較試行の取得状況');window.geometry('880x660')
        box=ScrolledText(window,wrap='word',font=('Yu Gothic UI',11))
        box.pack(fill='both',expand=True,padx=14,pady=14)
        box.insert('1.0','集計できませんでした：'+error if error else render(report));box.configure(state='disabled')
    app.submit('plan_result',work,'保存済み比較試行の成功・失敗を集計しています…')
