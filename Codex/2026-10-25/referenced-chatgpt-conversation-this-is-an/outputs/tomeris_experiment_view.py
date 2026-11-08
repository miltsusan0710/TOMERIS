"""Explicit offline experiment runner with provenance revalidation."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from tomeris_bandit_lab import experiment
from tomeris_trial_export import dataset

def run(path,record_directory):
    with Path(path).open('rb') as f:raw=f.read(5000001)
    if len(raw)>5000000:raise ValueError('入力データは5MB以内です。')
    rows=json.loads(raw)
    if not isinstance(rows,list) or not rows or any(not isinstance(row,dict) for row in rows):raise ValueError('データ形式が不正です。')
    origins={r.get('origin') for r in rows}
    if origins=={'human_reviewed'}:
        manifest=[]
        for row in rows:
            provenance=row.get('provenance')
            if not isinstance(provenance,dict) or not isinstance(row.get('id'),str):raise ValueError('出典情報付きの書出しデータを選んでください。')
            manifest.append(dict(record=row['id']+'.json',review=provenance.get('review_file'),topic_id=row.get('topic_id'),split=row.get('split')))
        verified=dataset(record_directory,manifest)
        if rows!=verified:raise ValueError('書出しデータが元の記録・評価と一致しません。書き出し直してください。')
    elif origins!={'synthetic'}:raise ValueError('人工データと人が採点したデータは混ぜずに比較してください。')
    result=experiment(rows)
    result.update(dataset_sha256=hashlib.sha256(raw).hexdigest(),evaluated_at=datetime.now(timezone.utc).isoformat(),
                  source_verified=origins=={'human_reviewed'})
    return result

def summary(result):
    names={'search_order':'検索順','exact_title_first':'対象名一致優先'}
    lines=['人工データによる動作実験' if result['synthetic'] else '人が採点した記録でのオフライン実験',
           '概要の方針：'+names[result['policy']['overview']],'具体的質問の方針：'+names[result['policy']['specific']],
           f"評価データ：{result['test_count']}件",f"平均報酬：{result['test_reward']:.3f}",
           f"実験用の検索順固定：{result['baseline_reward']:.3f}",f"差：{result['delta']:+.3f}",
           'この数字は正答率ではありません。現行アプリとの比較ではなく、全検索の成功率も示しません。',
           '本文を取得できなかった試行は、この評価に含まれません。',
           'モデルの重み・通常の検索方法・記憶は変更していません。',
           '実用性能の向上やVoiceOSを超えたことの証明ではありません。',
           '入力データのSHA-256：'+result['dataset_sha256']]
    detail=result.get('evaluation')
    if detail:
        lines+=['評価報酬の内訳（正誤の判定ではありません）',
                f"検索順固定より高い {detail['higher']}件 ／ 同じ {detail['equal']}件 ／ 低い {detail['lower']}件",
                f"対象グループ {detail['topic_count']}件を等しく重み付けした平均差：{detail['topic_mean_delta']:+.3f}"]
        for context,label in [('overview','概要'),('specific','具体的質問')]:
            group=detail['by_context'][context]
            lines.append(f"{label}：{group['count']}件、平均差 {group['mean_delta']:+.3f}、低い報酬 {group['lower']}件")
        lines+=['質問ごとの比較値は保存する結果JSONに含まれます。統計的有意差や未知の質問への効果は判定していません。']
    return '\n\n'.join(lines)

def save(path,result):
    if result.get('production_enabled') is not False:raise ValueError('通常適用されていない実験結果だけ保存できます。')
    with Path(path).open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)

def open_experiment(app):
    from tkinter import Toplevel
    from tkinter import ttk,filedialog
    from tkinter.scrolledtext import ScrolledText
    if app.busy or app.closing:return
    path=filedialog.askopenfilename(parent=app.root,title='実験するデータセットを明示選択（通常回答には反映しません）',filetypes=[('JSON','*.json')])
    if not path:return
    def work():
        try:outcome=(run(path,app.service.data_dir/'research_trials'),None)
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:outcome=(None,str(exc))
        return done,outcome
    def done(outcome):
        if app.closing:return
        result,error=outcome
        window=Toplevel(app.root);window.title('学習実験の結果（通常回答には未適用）');window.geometry('820x660')
        text=ScrolledText(window,wrap='word',font=('Yu Gothic UI',11));text.pack(fill='both',expand=True,padx=14,pady=14)
        text.insert('1.0','実験を止めました：'+error if error else summary(result));text.configure(state='disabled')
        status=ttk.Label(window,text='');status.pack(fill='x',padx=14)
        def write():
            target=filedialog.asksaveasfilename(parent=window,title='実験結果を新規保存',initialfile='experiment_result.json',defaultextension='.json',filetypes=[('JSON','*.json')],confirmoverwrite=False)
            if not target:return
            try:save(target,result);status.configure(text='結果だけ保存しました。通常回答には適用していません。')
            except (OSError,ValueError) as exc:status.configure(text='保存できません：'+str(exc))
        if result:ttk.Button(window,text='結果を別ファイルに保存',command=write).pack(pady=12)
    app.submit('plan_result',work,'元資料と評価を検査し、オフライン実験を実行しています…')
