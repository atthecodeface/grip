import os, sys, argparse
import lib.command
class make(lib.command.GripCommandBase):
    """
    Make something
    """
    names = ["make"]
    command_options = {
        ("args",):     {"nargs":argparse.REMAINDER, "help":'command to perform'},        
    }
    def execute(self, prog, parser, command_name, options, args):
        self.get_grip_repo(ensure_configured=True)
        os.chdir(self.grip_repo.path())
        args=["make","-f",self.grip_repo.grip_makefile_path()]
        args.extend(options.args)
        os.execvp("make",args)
        pass

class shell(lib.command.GripCommandBase):
    """
    Execute a shell
    """
    names = ["shell"]
    command_options = {
        ("--shell",):      {"help":"Shell to invoke, defaulting to bash", "default":"bash"},
        ("args",):         {"nargs":argparse.REMAINDER, "help":'additional arguments for bash'},        
    }
    def execute(self, prog, parser, command_name, options, args):
        self.get_grip_repo(ensure_configured=True)
        env = {}
        for (k,v) in os.environ.items():
            env[k] = v
            pass
        for (k,v) in self.grip_repo.grip_env_iter():
            env[k] = v
            pass
        args = [options.shell]
        args.extend(options.args)
        os.execvpe(options.shell, args, env)
        pass

