import os
from pathlib import Path
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
        if checkoutname is None: dest=None
        else: dest = Path(checkoutname)
        branch       = self.options.branch
        grip_repo    = lib.grip.Toplevel.clone(options=self.options, repo_url=repo_url, dest=dest, branch=branch, invocation=self.invocation)
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
        ("--force",):         {"dest":"force_configure", "action":"store_true", "default":False, "help":"a configure grip repo may not safely be configured again; use this option to configure again, but only with the current configuration", "default":None},
        ("configuration",):   {"nargs":"?", "help":"specify a configuration to check out - if not supplied, use default from grip.toml", "default":None},
    }
    class ConfigureOptions(Options):
        configuration : Optional[str]
    options : ConfigureOptions
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(ensure_configured=False)
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
        self.get_grip_repo()
        self.grip_repo.reconfigure()
        return 0
        pass
