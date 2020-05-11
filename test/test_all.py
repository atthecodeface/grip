#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, unittest
# from .test_grip_desc import test_suite as grip_desc_test_suite
import importlib

log_dir       = os.environ["TESTS_LOG_DIR"]
#from .test_grip  import *
from .test_git   import *
#from .test_state_file  import *
# from .test_grip_desc import TestUnconfigured, TestConfigured, TestConfiguredSubrepos, TestStages

def add_test_suite(module_name:str)->None:
    m = importlib.import_module(module_name, package=__package__)
    if not hasattr(m,"test_suite"):
        raise Exception("Failed to import test_suite from %s - it did not have at test_suite attribute"%module_name)
    for t in m.test_suite:
        if hasattr(m,t):
            globals()[t]=getattr(m,t)
            pass
        pass
    pass
add_test_suite(".test_grip_desc")

if __name__ == "__main__":
    unittest.main()
    pass
