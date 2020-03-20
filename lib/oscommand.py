#a Imports
import sys, os, re
import subprocess
from .verbose import info

#a OSCommand
class OSCommand:
    class NullOptions:
        verbose = False
        pass
    #c Error
    class Error(Exception):
        """
        Exception to capture the result of an OS command
        """
        def __init__(self, cmd):
            self.cmd = cmd
            pass
        pass
        #f __str__
        def __str__(self):
            return "Error in " + self.cmd.string_command_result()
        pass
    #f __init__
    def __init__(self, cmd, options=None, cwd=None, env=None, run=True, stderr_output_indicates_error=True, input_data=None):
        """
        Run an OS command in a subprocess shell
        """
        if options is None: options=self.NullOptions()
        self.options = options
        self.stderr_output_indicates_error = stderr_output_indicates_error
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.process = None
        if run:
            self.start_process()
            self.run(input_data=input_data)
            pass
        pass
    #f start_process
    def start_process(self):
        info(self.options, "Executing command \"%s\":" % self.cmd)
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
    def output_string(self, s, max_lines=100):
        sl = s.rstrip("\n").split("\n")
        if len(sl)==1: return sl[0]
        append = ""
        if len(sl)>max_lines:
            append = "\\n..."
            sl = sl[:max_lines]
            pass
        return "\\n".join(sl)
    #f string_command_result
    def string_command_result(self):
        r = ""
        r += "OS Command '%s' completed\n" % (self.cmd)
        r += "  Return code %d\n" % (self.rc)
        r += "  Stdout: %s\n"     % (self.output_string(self.stdout))
        r += "  Stderr: %s\n"     % (self.output_string(self.stderr))
        return r
    #f error_output
    def error_output(self):
        return self.stderr
    #f run
    def run(self, input_data=None):
        (self.stdout, self.stderr) = self.process.communicate(input_data)
        self.stdout = self.stdout.decode()
        self.stderr = self.stderr.decode()
        self.rc                    = self.process.wait()
        info(self.options, self.string_command_result())
        pass
    #f result
    def result(self):
        had_error   = (self.rc!=0)
        if len(self.stderr)>0 and self.stderr_output_indicates_error:
            had_error=True
            pass
        if had_error:
            raise self.Error(self)
        return self.stdout
    #f All done
    pass

#a Export some things
OSCommandError = OSCommand.Error

#a Toplevel
def command(options, cmd, **kwargs):
    cmd = OSCommand(options=options, cmd=cmd, run=True, **kwargs)
    return cmd.result()
