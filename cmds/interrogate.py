import os, sys, shlex
import lib.command
import lib.repo
class root(lib.command.GripCommandBase):
    """
    Find the root of the grip repository
    """
    names = ["root"]
    command_options = {
        ("path",):      {"nargs":"?", "help":"file or directory within a grip repostiory whose root is to be found (default is working directory)", "default":None},
    }
    def execute(self, prog, parser, command_name, options, args):
        path = options.path
        if path is None:
            path = os.path.abspath(os.getcwd())
            pass
        if os.path.isfile(path): path=os.path.dirname(path)
        grip_repo = lib.repo.GripRepo(path=path)
        print(grip_repo.get_root(),end='')
        pass

class env(lib.command.GripCommandBase):
    """
    Returns the grip environment (what would be placed in the grip env shell file).

    This is suitable to be used with "eval `grip env`"
    """
    names = ["env"]
    command_options = {
    }
    def execute(self, prog, parser, command_name, options, args):
        grip_repo = lib.repo.GripRepo(ensure_configured=True)
        for (k,v) in grip_repo.grip_env_iter():
            print('%s=%s; export %s'%(k,shlex.quote(v),k))
            pass
        pass
