#a Imports
import os
import io
from pathlib import Path

from lib.base import GripBase
from lib.options    import Options
from lib.log       import Log
from lib.os_command import OSCommand
from lib.git import Repository as GitRepo

from .filesystem import FileSystem, FileContent, EmptyContent
from .loggable import TestLog, Loggable
from .toml_file import Toml
from .git import RepoBuildContentFn
from .git import Repository as GitRepository

from typing import Type, List, Callable, Optional, Any, ClassVar, cast, Dict, IO

grip_dir  = os.environ["GRIP_DIR"]
grip_exec = os.path.join(grip_dir,"grip")

#c Grip Toml Class
class GripToml(Toml):
    def __init__(self, fs:FileSystem, **kwargs:Any):
        Toml.__init__(self, **kwargs)
        pass
    pass

#c Repository - Grip repo building class
class Repository(GitRepository):
    grip_toml : str = ""
    grip_toml_class : Type[GripToml]
    #f __init__
    def __init__(self, name:str, fs:FileSystem, log:TestLog, **kwargs:Any) -> None:
        GitRepository.__init__(self, name=name, fs=fs, log=log, **kwargs)
        pass
    #f git_init
    def git_init(self, init_content:Optional[RepoBuildContentFn]=None) -> 'Repository':
        GitRepository.git_init(self, init_content = self.init_content)
        return self
    #f grip_toml_content
    def grip_toml_content(self) -> FileContent:
        if hasattr(self, "grip_toml_class"):
            self.grip_toml = self.grip_toml_class(self.fs)._as_string()
            pass
        return FileContent(self.grip_toml)
    #f init_content
    @staticmethod
    def init_content(repo:'GitRepository') -> None:
        self = cast(Repository,repo)
        self.make_dir(Path(".grip"))
        self.create_file(Path(".grip/grip.toml"), content=self.grip_toml_content())
        self.git_command(cmd="add .grip/grip.toml")
        pass
    #f grip_command_full_result
    def grip_command_full_result(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> OSCommand:
        cmd = "%s --show-log --verbose %s"%(grip_exec, cmd)
        cwd = self.abspath
        if wd is not None: cwd = Path.joinpath(self.abspath, Path(wd))
        self.add_log_string("Test running grip command in wd '%s' of '%s'"%(str(cwd), cmd))
        os_cmd = OSCommand(cmd=cmd, cwd=str(cwd), log=self.logger(), **kwargs).run()
        return os_cmd
    #f grip_command
    def grip_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        os_cmd = self.grip_command_full_result(cmd=cmd, wd=wd, **kwargs)
        if os_cmd.rc()!=0: raise Exception("Command Rc non-zero for: %s"%(str(os_cmd)))
        return os_cmd.stdout()
    pass

#c GripBaseTest
class GripBaseTest(GripBase):
    files:Dict[str,str] = {}
    toml_dicts:Dict[str,Any]={}
    verbose_files :bool= False
    def __init__(self, log:Log, files:Dict[str,str]={}, toml_dicts:Dict[str,Any]={}):
        options =  Options()
        options._validate()
        git_repo  = GitRepo(path=Path("."), permit_no_remote=True)
        git_repo._path = Path(".")
        GripBase.__init__(self, options=options, log=log, git_repo=git_repo, branch_name=None)
        self.files = files
        pass
    def is_file(self, path:Path) -> bool:
        return str(path) in self.files
    def open(self, path:Path, mode:str="r") -> IO[str]:
        if self.verbose_files: print("open %s %s"%(str(path),mode))
        if mode!="r": raise Exception("Test has read-only string files")
        if str(path) in self.files:
            if self.verbose_files:  print("opened")
            return io.StringIO(self.files[str(path)])
        if self.verbose_files:  print("not found")
        raise FileNotFoundError("GripBaseTest has not file '%s'"%str(path))
    pass

