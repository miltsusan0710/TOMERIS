from pathlib import Path
p=Path('outputs/tomeris_topic_settings.py');s=p.read_text(encoding='utf-8').replace('topics=list(topics)','topics=topics');p.write_text(s,encoding='utf-8')
p=Path('outputs/test_desktop_topic_settings.py');s=p.read_text(encoding='utf-8').replace("([],['a']*4", "('abc',[],['a']*4");p.write_text(s,encoding='utf-8')
