#a Imports
import sys, os, re
import subprocess
from typing import Type, Optional, Union, Dict, Any, Tuple
from .log import Log
from .options import Options

#a OSCommand
class OSCommand:
    # Result type - depends on include_rc
    Result = Union[str, Tuple[int,str]]
    #t Types of properties
    options : Optional[Options]
    log : Log
    cmd : str
    cwd : Optional[str]
    env : Optional[Dict[str,str]]
    include_rc : bool
    exception_on_error : bool
    process: Any
    stderr: str
    stdout: str
    rc : int
    #c NullOptions
    class NullOptions:
        verbose = False
        pass
    #c Error
    class Error(Exception):
        """
        Exception to capture the result of an OS command
        """
        def __init__(self, cmd:'OSCommand') -> None:
            self.cmd = cmd
            pass
        pass
        #f __str__
        def __str__(self) -> str:
            return "Error in " + self.cmd.string_command_result()
        pass
    #f __init__
    def __init__(self, cmd:str,
                 options:Optional[Options]=None,
                 cwd : Optional[str] = None,
                 env : Optional[Dict[str,str]] = None,
                 run : bool =True,
                 stderr_output_indicates_error : bool =True,
                 input_data : Optional[str] =None,
                 log : Optional[Log] = None,
                 exception_on_error :bool =True,
                 include_rc         :bool =False):
        """
        Run an OS command in a subprocess shell

        log can be None or a logger with an 'add_entry' method
        """
        if options is None: options=Options()
        self.options = options
        self.stderr_output_indicates_error = stderr_output_indicates_error
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.process = None
        if log is None: log=Log()
        self.log = log
        self.exception_on_error = exception_on_error
        self.include_rc = include_rc
        if run:
            self.start_process()
            self.run(input_data=input_data)
            pass
        pass
    #f start_process
    def start_process(self) -> None:
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
        pass
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
    #f string_command_result
    def string_command_result(self) -> str:
        r = ""
        r += "OS Command '%s' completed\n" % (self.cmd)
        r += "  WD %s\n" % (self.cwd)
        r += "  Return code %d\n" % (self.rc)
        r += "  Stdout: %s\n"     % (self.output_string(self.stdout))
        r += "  Stderr: %s\n"     % (self.output_string(self.stderr))
        return r
    #f error_output
    def error_output(self) -> str:
        return self.stderr
    #f return_code
    def return_code(self) -> int:
        return self.rc
    #f run
    def run(self, input_data:Optional[str]=None) -> None:
        (stdout, stderr) = self.process.communicate(input_data)
        self.stdout = stdout.decode()
        self.stderr = stderr.decode()
        self.rc                    = self.process.wait()
        if self.log: self.log.add_entry(self.log_result)
        pass
    #f result
    def result(self) -> Result:
        had_error   = (self.rc!=0)
        if len(self.stderr)>0 and self.stderr_output_indicates_error:
            had_error=True
            pass
        if had_error and self.exception_on_error:
            raise self.Error(self)
        if self.include_rc: return (self.rc, self.stdout)
        return self.stdout
    #f log_start
    def log_start(self, writer:Log.Writer) -> None:
        writer("OS command '%s' started in wd '%s' with env '%s'"%(self.cmd, self.cwd, self.env))
        pass
    #f log_result
    def log_result(self, writer:Log.Writer) -> None:
        self.log.write_multiline( writer=writer, s=self.string_command_result())
        pass
    #f All done
    pass

#a Export some things
OSCommandError = OSCommand.Error

#a Toplevel
def command(options:Optional[Options], cmd:str, **kwargs:Any) -> OSCommand.Result:
    cmd_result = OSCommand(options=options, cmd=cmd, run=True, **kwargs)
    return cmd_result.result()
