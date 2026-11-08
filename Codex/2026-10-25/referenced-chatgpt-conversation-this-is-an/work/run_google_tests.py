import sys,tempfile,unittest
from pathlib import Path
root=Path.cwd(); sys.path.insert(0,str(root/'outputs'))
tempfile.tempdir=str(root/'work'/'v07')
suite=unittest.TestSuite()
for pattern in ['test_desktop*.py','test_google_calendar.py']:
    suite.addTests(unittest.defaultTestLoader.discover(str(root/'outputs'),pattern=pattern))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
