#a Documentation
"""
Git repository creation and manipulation wrapper
"""

#a Imports
import os, re, inspect, sys, unittest
from pathlib import Path

from lib.log       import Log
from lib.options   import Options
from lib.git       import Repository as GitRepo
from lib.os_command  import OSCommand

from .filesystem  import FileSystem, FileContent, EmptyContent
from .loggable    import TestLog, Loggable

from typing import List, Callable, Optional, Any, ClassVar, cast

#c Git repo building class
RepoBuildContentFn = Callable[['Repository'],None]
class Repository(Loggable):
    readme_text = """
    This is a simple test git repo
    """
    name     : str
    abspath     : Path # Path within the actual file system
    relpath  : Path # Path within our FileSystem object
    git_repo : GitRepo
    #f __init__ - must do a git_init or git_clone afterwards
    def __init__(self, name:str, fs:FileSystem, log:TestLog, parent:Optional[Path]=None, **kwargs:Any):
        Loggable.__init__(self, log)
        self.name = name
        self.fs = fs
        self.relpath = Path(name)
        if parent is not None: self.relpath = parent.joinpath(self.relpath)
        self.abspath = self.fs.abspath(self.relpath)
        self.options = Options()
        self.options.verbose = False
        pass
    #f git_clone
    def git_clone(self, clone:Path, bare:bool=False, branch_name:str="master") -> 'Repository':
        self.add_log_string("Cloning %s"%str(clone))
        self.git_repo = GitRepo.clone(log=self.logger(), options=self.options, repo_url=str(clone), dest=self.abspath, bare=bare, new_branch_name=branch_name)
        if not bare:
            upstream =self.git_repo.get_upstream()
            if upstream is not None: self.git_repo.set_upstream_of_branch(branch_name, upstream)
            pass
        return self
    #f git_init - do a git init, add a readme, and commit
    def git_init(self, init_content:Optional[RepoBuildContentFn]=None) -> 'Repository':
        self.fs.make_dir(self.relpath)
        self.git_command(cmd="init")
        if init_content is not None: init_content(self)
        self.git_command(cmd="commit -m Init -a")
        self.git_repo = GitRepo(log=self.logger(), path=Path(self.abspath), permit_no_remote=True)
        return self
    #f add_readme
    @staticmethod
    def add_readme(self:'Repository', content:Optional[FileContent]=None) -> None:
        if content is None:
            file_content = FileContent(self.readme_text)
            pass
        else:
            file_content = content
            pass
        self.fs.create_file(path=Path(self.name).joinpath(Path("Readme.txt")), content=file_content)
        self.git_command(cmd="add Readme.txt")
        pass
    #f bare_clone
    def bare_clone(self) -> 'Repository':
        self.add_log_string("Bare clone of %s of path %s"%(self.name, str(self.abspath)))
        return self.__class__(name="%s.git"%(self.name), fs=self.fs, log=self.logger()).git_clone(clone=self.abspath, bare=True)
    #f make_dir
    def make_dir(self, path:Path) -> None:
        path = self.relpath.joinpath(path)
        self.add_log_string("Making directory %s"%str(path))
        self.fs.make_dir(path=path)
        pass
    #f create_file
    def create_file(self, path:Path, content:FileContent) -> None:
        path = self.relpath.joinpath(path)
        self.add_log_string("Creating file %s"%str(path))
        self.fs.create_file(path=path, content=content)
        pass
    #f append_to_file
    def append_to_file(self, path:Path, content:FileContent) -> None:
        path = self.relpath.joinpath(path)
        self.add_log_string("Appending to file %s"%str(path))
        self.fs.append_to_file(path, content=content)
        pass
    #f git_command
    def git_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        cwd = self.abspath
        if wd is not None: cwd = Path.joinpath(self.abspath, Path(wd))
        self.add_log_string("Test running git command in wd '%s' of '%s'"%(str(cwd), cmd))
        os_cmd = OSCommand(cmd="git %s"%cmd, cwd=str(cwd), log=self.logger(), **kwargs).run()
        if os_cmd.rc()!=0: raise Exception("Command Rc non-zero for: %s"%(str(os_cmd)))
        return os_cmd.stdout()
    #f git_command_allow_stderr
    def git_command_allow_stderr(self, cmd:str, **kwargs:Any) -> str:
        return self.git_command(cmd=cmd, **kwargs)
    pass

