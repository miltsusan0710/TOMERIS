from pathlib import Path
p=Path('outputs/tomeris_methods_ui.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('通常の調査に使う方法です。Wikipediaは百科事典内の検索です。\\nAPIは利用枠を消費し、提供元の設定によって料金が発生します。','調査に使う方法を選択します。\\nAPIは利用枠を消費し、料金が発生する場合があります。')
s=s.replace('キー欄が空なら現在のキーを維持します。保存はこの起動中のみ。\\nGoogle APIの実接続はキーと利用可能なモデルの設定後に確認します。','キーはこの起動中のみ保持。空欄なら現在のキーを維持します。')
s=s.replace('wraplength=580)',"wraplength=580,font=('Yu Gothic UI',9))")
s=s.replace('ttk.Label(fields,text=label)',"ttk.Label(fields,text=label,font=('Yu Gothic UI',9))")
s=s.replace("ttk.Label(queryframe,text='検索する文章（この文章だけを外部へ送ります）')","ttk.Label(queryframe,text='検索する文章（この文章だけを外部へ送ります）',font=('Yu Gothic UI',9))")
p.write_text(s,encoding='utf-8')
