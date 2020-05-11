#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, unittest
import importlib

from .test_state_file  import *
from typing import Any
def add_test_suite(module_name:str)->None:
    # typing will assume m is an empty module and so will abort on m.test_suite
    m : Any = importlib.import_module(module_name, package=__package__)
    if not hasattr(m,"test_suite"):
        raise Exception("Failed to import test_suite from %s - it did not have at test_suite attribute"%module_name)
    for t in m.test_suite :
        globals()[t.__name__]=t
        pass
    pass

add_test_suite(".test_grip_desc")
add_test_suite(".test_git")
add_test_suite(".test_grip")

if __name__ == "__main__":
    unittest.main()
    pass
