#a Imports
import os, time
from pathlib import Path

from .log         import Log
from .verbose     import Verbose
from .options     import Options
from .exceptions  import *
from typing import Type, List, Dict, Iterable, Optional, Any, Tuple, IO
from .git import Repository as GitRepository

#c GripBase
class GripBase:
    #v Static properties
    grip_dir_name = ".grip"
    grip_toml_filename   = "grip.toml"
    state_toml_filename  = "state.toml"
    config_toml_filename = "local.config.toml"
    grip_env_filename    = "local.env.sh"
    grip_log_filename    = "local.log"
    makefile_stamps_dirname = "local.makefile_stamps"
    grip_makefile_filename = "local.grip_makefile"
    grip_makefile_env_filename = "local.grip_makefile.env"
    #v Instance properties
    log         : Log
    options     : Options
    verbose     : Verbose
    git_repo    : GitRepository
    branch_name : Optional[str]
    #f __init__
    def __init__(self, options:Options, log:Log, git_repo:GitRepository, branch_name:Optional[str]=None):
        self.log=log
        self.options=options
        self.verbose=options.get_verbose_fn()
        self.git_repo = git_repo
        self.branch_name = branch_name
        pass
    #f log_to_logfile
    def log_to_logfile(self) -> None:
        """
        Invoked to append the log to the local logfile
        """
        with open(self.grip_path(self.grip_log_filename),"a") as f:
            print("",file=f)
            print("*"*80,file=f)
            self.log.dump(f)
            pass
        pass
    #f add_log_string
    def add_log_string(self, s:str) -> None:
        if self.log: self.log.add_entry_string(s)
        pass
    #f path
    def path(self, filenames:List[str]=[]) -> str:
        assert self.git_repo is not None
        return self.git_repo.filename(filenames)
    #f grip_path
    def grip_path(self, filename:str) -> str:
        return self.path([self.grip_dir_name, filename])
    #f grip_makefile_path
    def grip_makefile_path(self) -> str:
        return self.grip_path(self.grip_makefile_filename)
    #f set_branch_name
    def set_branch_name(self, branch_name:str) -> None:
        self.branch_name = branch_name
        pass
    #f get_branch_name - get string branch name
    def get_branch_name(self) -> str:
        """
        Get branch name - it must have been set
        """
        assert self.branch_name is not None
        return self.branch_name
    #f get_git_repo - get git repo
    def get_git_repo(self) -> GitRepository:
        assert self.git_repo is not None
        return self.git_repo
    #f open
    def open(self, path:Path, mode:str="r") -> IO[str]:
        return path.open(mode)
    #f is_file
    def is_file(self, path:Path)->bool:
        return path.is_file()
    #f All done
    pass
