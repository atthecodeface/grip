#a Imports
import os
from pathlib import Path

from lib.log       import Log

from .filesystem import FileSystem, FileContent, EmptyContent
from .loggable import TestLog, Loggable
from .os_command import OSCommand
from .git import RepoBuildContentFn
from .git import Repository as GitRepository

from typing import List, Callable, Optional, Any, ClassVar, cast

grip_dir  = os.environ["GRIP_DIR"]
grip_exec = os.path.join(grip_dir,"grip")

#c Grip repo building class
class Repository(GitRepository):
    grip_toml = """
    name = "test_grip"
    default_config  = "cfg0"
    configs         = ["cfg0","cfg1"]
    base_repos      = ["d1"]
    stages          = ["install"]
    workflow        = "readonly"
    env             = {{D2ENV="d2"}}
    [config.cfg1]
    repos = ["d2"]
    d2.install = {{requires=[], wd="", exec="do_exec"}}
    [repo]
    d1 = {{ url="{fs_path}/d_1.git", branch="master", path="d1" }}
    d2 = {{ url="{fs_path}/d_2.git", branch="master", path="%D2ENV%" }}
    """
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
        self.create_file(Path(".grip/grip.toml"), content=FileContent(self.grip_toml.format(fs_path=self.fs.path)))
        self.git_command(wd=".grip", cmd="add grip.toml")
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

