import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_plans import DesktopService
with tempfile.TemporaryDirectory(dir='work/v07') as directory:
    service=DesktopService(directory,source=Path(directory)/'absent.json')
    try:
        names=service.models()
        if 'qwen2.5:3b' not in names:
            raise RuntimeError('qwen2.5:3b is unavailable')
        draft=service.draft_plan('トメリスの使い方を試す',30,'qwen2.5:3b')
        print(draft)
        assert not (Path(directory)/'daily_plans.json').exists()
        print('Live proposal validated; no plan saved.')
    finally:
        service.close()
