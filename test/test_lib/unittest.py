import os, unittest
from .loggable import TestLog

from typing import Type, Dict, List, Any, Callable

log_dir       = os.environ["TESTS_LOG_DIR"]

#c Extend unittest.TestCase
class TestCase(unittest.TestCase):
    _fqn : str
    _logger : TestLog
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpSubClass(cls, subclass:Type['TestCase']) -> None:
        if not hasattr(cls,"_logger"):
            subclass._fqn = subclass.__module__+"."+subclass.__qualname__
            subclass._logger   = TestLog(os.path.join(log_dir,"%s.log"%subclass._fqn))
            pass
        subclass._logger.add_log_string("* "*30)
        subclass._logger.add_log_string("Setting up test class %s"%subclass._fqn)
        subclass._logger.add_log_string("* "*30)
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownSubClass(cls,subclass:Type['TestCase']) -> None:
        subclass._logger.tidy()
        pass
    #f setUp
    def setUp(self) -> None:
        self._logger.add_log_string("- "*30)
        self._logger.add_log_string("Setting up test %s"%str(self))
        self._logger.add_log_string("- "*30)
        pass
    #f tearDown
    def tearDown(self) -> None:
        self._logger.add_log_string("Completed test %s"%str(self))
        self._logger.add_log_string("+ "*30)
        pass
    pass
#c Stuff from test_utils
import unittest
from collections import namedtuple
AKV = Dict[str,Any]
AKV_has = Callable[[Any,str],bool]
AKV_get = Callable[[Any,str],Any]
class UnitTestObject(unittest.TestCase):
    def _test_asserts(self, d:Dict[str,Any], akv:AKV, reason:str, has_element_fn:AKV_has, get_element_fn:AKV_get ) -> None:
        # print("_test_asserts %s:%s:%s"%(reason, str(akv),str(d)))
        if type(akv) is not dict:
            self.fail("Bug in test - reason '%s' - test data '%s' is not a dictionary (type '%s'), but element is type '%s'"%(reason, str(akv),str(type(akv)),str(type(d))))
            return
        for (k,v) in akv.items():
            if has_element_fn(d,k):
                dv = get_element_fn(d,k)
                if type(dv) in [str,int]:
                    self.assertEqual(dv,v,"Mismatch in %s for key %s"%(reason,k))
                    pass
                elif type(dv) is list:
                    self.assertEqual(dv,v,"List ! %s for key %s"%(reason,k))
                    pass
                elif type(dv) is dict:
                    self._test_dict_asserts(dv,v,"%s.%s"%(reason,k))
                    pass
                else:
                    self._test_obj_asserts(dv,v,"%s.%s"%(reason,k))
                    pass
                pass
            else:
                self.fail("%s (of type %s) expected to have key %s but it did not"%(reason, str(type(d)), k))
                pass
            pass
        pass
    def _test_dict_asserts(self, d:Dict[str,Any], akv:AKV, reason:str ) -> None:
        return self._test_asserts(d, akv, reason, has_element_fn=(lambda d,k:k in d), get_element_fn=(lambda d,k:d[k]))
    def _test_obj_asserts(self, d:Dict[str,Any], akv:AKV, reason:str )->None:
        return self._test_asserts(d, akv, reason, has_element_fn=hasattr, get_element_fn=getattr)
    pass
