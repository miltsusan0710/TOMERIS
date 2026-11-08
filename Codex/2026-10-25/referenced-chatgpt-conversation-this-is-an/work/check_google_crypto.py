import ast
import sys
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
for name in ['tomeris_google.py','tomeris_google_ui.py','tomeris_desktop_v010.py']:
    ast.parse((Path('outputs')/name).read_text(encoding='utf-8-sig'))
from tomeris_google import protect
raw=b'tomeris-test-only-no-real-credentials'
sealed=protect(raw)
assert raw not in sealed
assert protect(sealed,decrypt=True)==raw
print('Syntax and Windows DPAPI round trip: OK')
