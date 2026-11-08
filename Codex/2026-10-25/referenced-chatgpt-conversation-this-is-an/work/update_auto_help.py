from pathlib import Path
p=Path('outputs/tomeris_desktop_v028.py');s=p.read_text(encoding='utf-8').replace('初期設定はWikipediaです。','初期設定は自動選択です。「Googleで」「Wikipediaで」などの指定を優先します。').replace('調査方法は上部メニューで選べます。検索語・指定URLを外部へ送ります。','調査方法は自動選択します。方法を指定した質問では指定を優先します。検索語・指定URLを外部へ送ります。');p.write_text(s,encoding='utf-8')
