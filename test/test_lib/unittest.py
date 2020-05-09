import os, unittest
from .loggable import TestLog

from typing import Type

log_dir       = os.environ["TESTS_LOG_DIR"]

#c Extend unittest.TestCase
class TestCase(unittest.TestCase):
    _fqn : str
    _logger : TestLog
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpSubClass(cls, subclass:Type['TestCase']) -> None:
        if not hasattr(cls,"_logger"):
            cls._fqn = subclass.__module__+"."+subclass.__qualname__
            cls._logger   = TestLog(os.path.join(log_dir,"%s.log"%cls._fqn))
            pass
        cls._logger.add_log_string("* "*30)
        cls._logger.add_log_string("Setting up test class %s"%cls._fqn)
        cls._logger.add_log_string("* "*30)
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownSubClass(cls,subclass:Type['TestCase']) -> None:
        cls._logger.tidy()
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
