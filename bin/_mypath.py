import sys
import os.path

thisdir = os.path.dirname(__file__)
devdir = os.path.abspath(os.path.join(thisdir, '..'))

if devdir not in sys.path:
    sys.path.insert(0, devdir)
