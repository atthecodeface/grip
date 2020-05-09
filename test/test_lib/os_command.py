from typing import List, Optional, Any

#a Imports
import sys, os, re
import subprocess
from typing import Type, Optional, Union, Dict, Any, Tuple
from lib.log import Log

#a OSCommand
class OSCommand:
    #t Types of properties
    log : Log
    cmd : str
    cwd : Optional[str]
    env : Optional[Dict[str,str]]
    input_data : Optional[str]
    completed : bool
    # process: Any
    _stderr: str
    _stdout: str
    _rc : int
    #f __init__
    def __init__(self,
                 cmd:str,
                 cwd : Optional[str] = None,
                 env : Optional[Dict[str,str]] = None,
                 input_data : Optional[str] =None,
                 log : Optional[Log] = None):
        """
        Run an OS command in a subprocess shell

        log can be None or a logger with an 'add_entry' method
        """
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.input_data = input_data
        if log is None: log=Log()
        self.log = log
        self.completed = False
        pass
    #f log_start
    def log_start(self, writer:Log.Writer) -> None:
        writer("OS command '%s' started in wd '%s' with env '%s'"%(self.cmd, self.cwd, self.env))
        pass
    #f log_result
    def log_result(self, writer:Log.Writer) -> None:
        self.log.write_multiline( writer=writer, s=self.string_command_result())
        pass
    #f run
    def run(self, input_data:Optional[str]=None) -> 'OSCommand':
        if input_data is None: input_data=self.input_data
        if self.log: self.log.add_entry(self.log_start)
        self.process = subprocess.Popen(args=self.cmd,
                                        shell=True, # So that args is a string not a list
                                        cwd=self.cwd,
                                        env=self.env,
                                        stdin =subprocess.PIPE, # Create new stdin; we can
                                        stdout=subprocess.PIPE, # Create stdout to be captured
                                        stderr=subprocess.PIPE, # Create stderr to be captured
                                        bufsize=16*1024,  # Large buffer for input and output
                                        close_fds=True,   # Don't inherit other file handles
                                        )
        input_data_bytes = None
        if self.input_data is not None:
            input_data_bytes = self.input_data.encode()
            pass
        (stdout, stderr) = self.process.communicate(input_data_bytes)
        self._stdout = stdout.decode()
        self._stderr = stderr.decode()
        self._rc     = self.process.wait()
        self.completed = True
        if self.log: self.log.add_entry(self.log_result)
        return self
    #f stdout
    def stdout(self) -> str:
        return self._stdout
    #f stderr
    def stderr(self) -> str:
        return self._stderr
    #f rc
    def rc(self) -> int:
        return self._rc
    #f output_string
    def output_string(self, s:str, max_lines:int=100) -> str:
        sl = s.rstrip("\n").split("\n")
        if len(sl)==1: return sl[0]
        append = ""
        if len(sl)>max_lines:
            append = "\\n..."
            sl = sl[:max_lines]
            pass
        return "\\n".join(sl)
    #f __str__
    def __str__(self) -> str:
        r = ""
        r += "[%s]:%s:"%(self.cwd, self.cmd)
        if self.completed:
            r += " -> %d [o:%d, e:%d]"%(self._rc, len(self._stdout), len(self._stderr))
        return r
    #f string_command_result
    def string_command_result(self) -> str:
        r = ""
        r += "OS Command '%s' completed\n" % (self.cmd)
        r += "  WD %s\n" % (self.cwd)
        r += "  Return code %d\n" % (self._rc)
        r += "  Stdout: %s\n"     % (self.output_string(self._stdout))
        r += "  Stderr: %s\n"     % (self.output_string(self._stderr))
        return r
    #f All done
    pass


#a Tests stuff
class TestResult:
    def __init__(self, reason:str):
        pass
    pass
OptTestResult = Optional[TestResult]
