import sys,tempfile,unittest,ast
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root/'outputs'))
tempfile.tempdir=str(root/'work'/'v07')
for name in ['tomeris_plans.py','tomeris_desktop_v091.py','tomeris_desktop.py']:
    ast.parse((root/'outputs'/name).read_text(encoding='utf-8-sig'))
suite=unittest.defaultTestLoader.discover(str(root/'outputs'),pattern='test_desktop*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
