import sys
import tempfile
from pathlib import Path
import unittest
root=Path.cwd()
sys.path.insert(0,str(root/'outputs'))
tempfile.tempdir=str(root/'work'/'v07')
suite=unittest.defaultTestLoader.discover(str(root/'outputs'),pattern='test_v081*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())


