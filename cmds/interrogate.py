import os, sys, shlex
import lib.command
import lib.repo
import lib.repodesc
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
        self.get_grip_repo(path=path)
        print(self.grip_repo.get_root(),end='')
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
        self.get_grip_repo(ensure_configured=True)
        for (k,v) in self.grip_repo.grip_env_iter():
            print('%s=%s; export %s'%(k,shlex.quote(v),k))
            pass
        pass

class doc(lib.command.GripCommandBase):
    """
    Prints the documentation
    """
    names = ["doc"]
    command_options = {
    }
    def execute(self, prog, parser, command_name, options, args):
        def f(e):
            print("Warning: %s"%str(e))
            e.grip_env.get_root().add_values({e.key:""})
            return ("",)
        self.get_grip_repo(ensure_configured=False, error_handler=lib.repodesc.GripEnvValueError.error_handler(f))
        grip_repo_doc = self.grip_repo.get_doc()
        if self.grip_repo.is_configured():
            print("This is a configured grip repository, with a name of '%s', using configuration '%s'"%(self.grip_repo.get_name(), self.grip_repo.get_config_name()))
            pass
        else:
            print("This is an unconfigured grip repository, with a name of '%s'"%(self.grip_repo.get_name()))
            print("It supports the following configurations: %s"%(" ".join(self.grip_repo.get_configurations())))
            pass
        for (n,v) in grip_repo_doc:
            if n is not None:
                print("\n%s"%n)
                pass
            print(v)
            pass
        pass
