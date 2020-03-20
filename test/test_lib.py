#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, re, inspect, sys, unittest

grip_test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
grip_dir      = os.path.dirname(grip_test_dir)
sys.path.append(grip_dir)

from lib.git       import RepoUnitTest
from lib.repodesc  import *
from lib.repostate import *
if __name__ == "__main__":
    unittest.main()
    pass
