import os
import lib.grip
from lib.command import GripCommandBase, ParsedCommand
from lib.options import Options
from typing import Optional, List

class clone(GripCommandBase):
    """
    Clone a grip repo (using git) and configure
    """
    names = ["checkout"]
    command_options = {
        ("repo_url",):      {"help":'repository to clone'},
        ("checkoutname",):  {"nargs":"?", "help":'destination name', "default":None},
        ("--config",):      {"dest":"config", "help":"specify a configuration to check out", "default":None},
        ("--branch",):      {"dest":"branch", "help":"specify a git branch of the main grip repo to check out", "default":None},
    }
    class CloneOptions(Options):
        repo_url    : str
        checkoutname : Optional[str]
        config       : Optional[str]
        branch       : Optional[str]
    options : CloneOptions
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        repo_url     = self.options.repo_url.rstrip('/')
        checkoutname = self.options.checkoutname
        branch       = self.options.branch
        grip_repo    = lib.grip.Toplevel.clone(options=self.options, repo_url=repo_url, branch=branch, path=None, dest=checkoutname, invocation=self.invocation)
        self.add_logger(grip_repo.log)
        #print(grip_repo.debug_repodesc())
        grip_repo.configure(config_name = self.options.config)
        return 0
    pass

class configure(GripCommandBase):
    """
    Configure a grip repo (using git) that has just been git cloned
    """
    names = ["configure"]
    command_options = {
        ("configuration",):      {"nargs":"?", "help":"specify a configuration to check out - if not supplied, use default from grip.toml", "default":None},
    }
    class ConfigureOptions(Options):
        configuration : Optional[str]
    options : ConfigureOptions
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.configure(config_name=self.options.configuration)
        return 0
        pass

class reconfigure(GripCommandBase):
    """
    Reconfigure a grip repo (using git) that has been configured before

    This does not checkout the repositories; it only rebuilds local files. Hence you cannot change the configuration of the grip repo.
    """
    names = ["reconfigure"]
    # command_options = { }
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(path=os.path.abspath(os.getcwd()), ensure_configured=True)
        self.grip_repo.reconfigure()
        return 0
        pass
