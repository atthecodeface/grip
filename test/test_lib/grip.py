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
from .git import RepoBuildContentFn
from .git import Repository as GitRepository

from typing import List, Callable, Optional, Any, ClassVar, cast, Dict, IO

grip_dir  = os.environ["GRIP_DIR"]
grip_exec = os.path.join(grip_dir,"grip")

#c Grip repo building class
class Repository(GitRepository):
    grip_toml = ""
    #f __init__
    def __init__(self, name:str, fs:FileSystem, log:TestLog, **kwargs:Any) -> None:
        GitRepository.__init__(self, name=name, fs=fs, log=log, **kwargs)
        pass
    #f git_init
    def git_init(self, init_content:Optional[RepoBuildContentFn]=None) -> 'Repository':
        GitRepository.git_init(self, init_content = self.init_content)
        return self
    #f init_content
    @staticmethod
    def init_content(repo:'GitRepository') -> None:
        self = cast(Repository,repo)
        self.make_dir(Path(".grip"))
        self.create_file(Path(".grip/grip.toml"), content=FileContent(self.grip_toml))
        self.git_command(cmd="add .grip/grip.toml")
        pass
    #f grip_command
    def grip_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        cmd = "%s --show-log --verbose %s"%(grip_exec, cmd)
        cwd = self.abspath
        if wd is not None: cwd = Path.joinpath(self.abspath, Path(wd))
        self.add_log_string("Test running grip command in wd '%s' of '%s'"%(str(cwd), cmd))
        os_cmd = OSCommand(cmd=cmd, cwd=str(cwd), log=self.logger(), **kwargs).run()
        if os_cmd.rc()!=0: raise Exception("Command Rc non-zero for: %s"%(str(os_cmd)))
        return os_cmd.stdout()
    pass

#c GripBaseTest
class GripBaseTest(GripBase):
    files:Dict[str,str] = {}
    toml_dicts:Dict[str,Any]={}
    def __init__(self, log:Log, files:Dict[str,str]={}, toml_dicts:Dict[str,Any]={}):
        options =  Options()
        options._validate()
        git_repo  = GitRepo(path=Path(".").resolve(), permit_no_remote=True)
        GripBase.__init__(self, options=options, log=log, git_repo=git_repo, branch_name=None)
        self.files = files
        pass
    def open(self, path:Path, mode:str="r") -> IO[str]:
        print("open %s"%str(path))
        if str(path) in self.files:
            return io.StringIO(self.files[str(path)])
        raise FileNotFoundError("GripBaseTest has not file '%s'"%str(path))
    pass

