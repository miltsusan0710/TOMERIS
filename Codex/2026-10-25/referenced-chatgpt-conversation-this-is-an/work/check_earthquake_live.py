from pathlib import Path
import sys
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_earthquake import fetch_latest,EarthquakeError
try:answer=fetch_latest()
except EarthquakeError as exc:answer='今の地震の震源は未確認です。'+str(exc)
Path('work/earthquake_live_check.txt').write_text(answer,encoding='utf-8')
print(answer)
