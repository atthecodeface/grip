"""
Logging class
"""

#a Imports
from pathlib  import Path
from lib.log  import Log
from typing   import List, Optional, Any

#c TestLog class
class TestLog(Log):
    filename : str
    def __init__(self, filename:str="test.log") -> None:
        Log.__init__(self)
        self.set_tidy(self.log_to_logfile)
        self.filename = filename
        with open(self.filename,"w") as f: pass
        pass
    #f add_log_string
    def add_log_string(self, s:str) -> None:
        return self.add_entry_string(s)
    #f log_to_logfile
    def log_to_logfile(self) -> None:
        """
        Invoked to append the log to the local logfile
        """
        with open(self.filename,"a") as f:
            print("",file=f)
            print("*"*80,file=f)
            self.dump(f)
            pass
        pass
    pass

#c Base loggable class
class Loggable(object):
    _logger_verbose : bool = False
    _logger_log : TestLog
    #f __init__
    def __init__(self, logger:TestLog):
        self._logger_log = logger
    #f add_log_string
    def add_log_string(self, s:str) -> None:
        if self._logger_verbose: print(s)
        return self._logger_log.add_log_string(s)
    #f log_flush
    def log_flush(self) -> None:
        return self._logger_log.tidy(reset=True)
    #f log_file_contents
    def log_file_contents(self, p:Path, prefix:str="") -> None:
        self.log_flush()
        with p.open() as f:
            for l in f:
                self.add_log_string("%s%s"%(prefix,l.rstrip()))
                pass
            pass
        self.log_flush()
        pass
    #f logger
    def logger(self) -> TestLog:
        return self._logger_log
    pass

