import sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tomeris_evaluate_behavior as evaluation
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    case=dict(id='intentional_negative_control',category='検査器検証',turns=['計算: 2+2'],required=['結果：999'],forbidden=[])
    with patch.object(evaluation,'CASES',[case]):result=evaluation.run(folder)
    assert result['cases'][0]['status']=='failed'
    assert all(c['status']=='not_evaluated' for c in result['model_cases'])
print('Negative control correctly failed; unevaluated model cases remain unevaluated.')
