import os
import re
import lib.command
import lib.repo
class clone(lib.command.GripCommandBase):
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
    def execute(self, prog, parser, command_name, options, args):
        repo_url     = options.repo_url.rstrip('/')
        checkoutname = options.checkoutname
        branch       = options.branch
        grip_repo    = lib.repo.GripRepo.clone(options, repo_url, branch, path=None, dest=checkoutname)
        print(grip_repo.debug_repodesc())
        grip_repo.configure(config_name = options.config)
        pass
    pass

class configure(lib.command.GripCommandBase):
    """
    Configure a grip repo (using git) that has just been git cloned
    """
    names = ["configure"]
    command_options = {
        ("configuration",):      {"nargs":"?", "help":"specify a configuration to check out - if not supplied, use default from grip.toml", "default":None},
    }
    def execute(self, prog, parser, command_name, options, args):
        grip_repo = lib.repo.GripRepo(path=os.path.abspath(os.getcwd()))
        grip_repo.configure(options, config_name = options.configuration)
        pass
