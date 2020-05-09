#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, unittest

log_dir       = os.environ["TESTS_LOG_DIR"]
from .test_grip  import *
from .test_git   import *
#from lib.repodesc  import *
#from lib.repostate import *
if __name__ == "__main__":
    unittest.main()
    pass
