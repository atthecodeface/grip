import os, sys, argparse
from lib.command import GripCommandBase, ParsedCommand
from lib.options import Options
from typing import Optional, List

class make(GripCommandBase):
    """
    Make something
    """
    names = ["make"]
    command_options = {
        ("args",):     {"nargs":argparse.REMAINDER, "help":'command to perform'},
    }
    class MakeOptions(Options):
        args : List[str]
    options : MakeOptions
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(ensure_configured=True)
        path = self.grip_repo.path()
        os.chdir(path)
        args=["make","-f",str(self.grip_repo.grip_makefile_path())]
        args.extend(self.options.args)
        self.grip_repo.verbose.info("Entering "+str(path))
        self.grip_repo.verbose.info("Executing "+" ".join(args))
        os.execvp("make",args)
        return None

class shell(GripCommandBase):
    """
    Execute a shell
    """
    names = ["shell"]
    command_options = {
        ("--shell",):      {"help":"Shell to invoke, defaulting to bash", "default":"bash"},
        ("args",):         {"nargs":argparse.REMAINDER, "help":'additional arguments for bash'},
    }
    class ShellOptions(Options):
        shell : str
        args  : List[str]
    options : ShellOptions
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(ensure_configured=True)
        self.grip_repo.invoke_shell(self.options.shell, self.options.args)
        return 0

