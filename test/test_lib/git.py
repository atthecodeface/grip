#a Documentation
"""
Git repository creation and manipulation wrapper
"""

#a Imports
import os, re, inspect, sys, unittest

from lib.log       import Log
from lib.options   import Options
from lib.git       import Repository as GitRepo

from .filesystem  import FileSystem, PathList, FileContent, EmptyContent
from .loggable    import TestLog, Loggable
from .os_command  import OSCommand

from typing import List, Callable, Optional, Any, ClassVar, cast

#c Git repo building class
RepoBuildContentFn = Callable[['Repository'],None]
class Repository(Loggable):
    readme_text = """
    This is a simple test git repo
    """
    #f __init__
    def __init__(self, name:str, fs:FileSystem, log:TestLog, parent_dirs:List[str]=[], clone:Optional[str]=None, bare:bool=False, init_content:Optional[RepoBuildContentFn]=None, branch_name:str="master") -> None:
        Loggable.__init__(self, log)
        self.name = name
        self.path = fs.abspath(parent_dirs+[name])
        self.fs = fs
        self.options = Options()
        self.options.verbose = False
        if clone is None:
            self.fs.make_dir([self.name])
            self.git_command(cmd="init")
            if init_content is not None:
                init_content(self)
                pass
            else:
                self.fs.create_file(paths=[self.name,"Readme.txt"], content=FileContent(self.readme_text))
                self.git_command(cmd="add Readme.txt")
                pass
            self.git_command(cmd="commit -m Init -a")
            self.git_repo = GitRepo(log=self.logger(), path_str=self.path, permit_no_remote=True)
            pass
        else:
            self.git_repo = GitRepo.clone(log=self.logger(), options=self.options, repo_url=clone, dest=self.path, bare=bare, new_branch_name=branch_name)
            if not bare:
                upstream =self.git_repo.get_upstream()
                if upstream is not None: self.git_repo.set_upstream_of_branch(branch_name, upstream)
            pass
        pass
    #f bare_clone
    def bare_clone(self) -> 'Repository':
        return  self.__class__(name="%s.git"%(self.name),fs=self.fs, log=self.logger(), clone=self.path, bare=True)
    #f make_dir
    def make_dir(self, paths:PathList) -> None:
        self.add_log_string("Making directory %s"%str([self.name]+paths))
        self.fs.make_dir([self.name]+paths)
        pass
    #f create_file
    def create_file(self, paths:PathList, content:FileContent) -> None:
        self.add_log_string("Creating file %s"%str([self.name]+paths))
        self.fs.create_file(paths=[self.name]+paths, content=content)
        pass
    #f append_to_file
    def append_to_file(self, paths:PathList, content:FileContent) -> None:
        self.add_log_string("Appending to file %s"%str([self.name]+paths))
        self.fs.append_to_file([self.name]+paths, content=content)
        pass
    #f git_command
    def git_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        cwd = self.path
        if wd is not None: cwd = os.path.join(self.path, wd)
        self.add_log_string("Test running git command in wd '%s' of '%s'"%(cwd, cmd))
        os_cmd = OSCommand(cmd="git %s"%cmd, cwd=cwd, log=self.logger(), **kwargs).run()
        if os_cmd.rc()!=0: raise Exception("Command Rc non-zero for: %s"%(str(os_cmd)))
        return os_cmd.stdout()
    #f git_command_allow_stderr
    def git_command_allow_stderr(self, cmd:str, **kwargs:Any) -> str:
        return self.git_command(cmd=cmd, **kwargs)
    pass

