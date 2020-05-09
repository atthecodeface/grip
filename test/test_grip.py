#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, re, inspect, sys, unittest

from lib.log       import Log
from lib.options   import Options
from lib.git       import Repository as GitRepo

from .test_lib.filesystem import FileSystem, PathList, FileContent, EmptyContent
from .test_lib.loggable import TestLog, Loggable
from .test_lib.os_command import OSCommand

from .test_lib.git import RepoBuildContentFn
from .test_lib.git import Repository as GitRepository

from typing import List, Callable, Optional, Any, ClassVar, cast

grip_dir      = os.environ["GRIP_DIR"]
log_dir       = os.environ["TESTS_LOG_DIR"]
test_logger   = TestLog(os.path.join(log_dir,"test_grip.log"))
sys.path.append(grip_dir)

#a Test classes
#c Grip repo building class
class GripRepoBuild(GitRepository):
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
        global grip_dir
        GitRepository.__init__(self, name=name, fs=fs, log=log, **kwargs)
        self.grip_exec = os.path.join(grip_dir,"grip")
        pass
    #f git_init
    def git_init(self, init_content:Optional[RepoBuildContentFn]=None) -> 'GripRepoBuild':
        GitRepository.git_init(self, init_content = self.init_content)
        return self
    #f init_content
    @staticmethod
    def init_content(repo:'GitRepository') -> None:
        self = cast(GripRepoBuild,repo)
        self.make_dir([".grip"])
        self.create_file(paths=[".grip","grip.toml"], content=FileContent(self.grip_toml.format(fs_path=self.fs.path)))
        self.git_command(wd=".grip", cmd="add grip.toml")
        pass
    #f grip_command
    def grip_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        cmd = "%s --show-log --verbose %s"%(self.grip_exec, cmd)
        cwd = self.path
        if wd is not None: cwd = os.path.join(self.path, wd)
        self.add_log_string("Test running grip command in wd '%s' of '%s'"%(cwd, cmd))
        os_cmd = OSCommand(cmd=cmd, cwd=cwd, log=test_logger, **kwargs).run()
        if os_cmd.rc()!=0: raise Exception("Command Rc non-zero for: %s"%(str(os_cmd)))
        return os_cmd.stdout()
    pass

#c Basic grip test case
class Test(unittest.TestCase):
    #v class properties
    cls_fs      : ClassVar[FileSystem]
    cls_d1      : ClassVar[GitRepository]
    cls_d1_bare : ClassVar[GitRepository]
    cls_d2      : ClassVar[GitRepository]
    cls_d2_bare : ClassVar[GitRepository]
    cls_g       : ClassVar[GripRepoBuild]
    cls_g_bare  : ClassVar[GitRepository]
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        try:
            fs = FileSystem()
            cls.cls_fs = fs
            cls.cls_d1       = GitRepository(name="d_1",fs=fs,parent_dirs=[],log=test_logger).git_init(GitRepository.add_readme)
            cls.cls_d1_bare  = cls.cls_d1.bare_clone()
            cls.cls_d2       = GitRepository(name="d_2",fs=fs,parent_dirs=[],log=test_logger).git_init(GitRepository.add_readme)
            cls.cls_d2_bare  = cls.cls_d2.bare_clone()
            cls.cls_g        = GripRepoBuild(name="grip_1",fs=fs,log=test_logger).git_init()
            cls.cls_g_bare   = cls.cls_g.bare_clone()
        except:
            test_logger.tidy()
            raise
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.cls_fs.cleanup()
        except:
            test_logger.tidy()
            raise
        test_logger.tidy()
        pass
    #f setUp
    def setUp(self) -> None:
        test_logger.add_log_string("- "*30)
        test_logger.add_log_string("Setting up test %s"%str(self))
        test_logger.add_log_string("- "*30)
        pass
    #f tearDown
    def tearDown(self) -> None:
        test_logger.add_log_string("Completed test %s"%str(self))
        test_logger.add_log_string("+ "*30)
        pass
    #f test_git_clone
    def test_git_clone(self) -> None:
        fs = FileSystem()
        d2 = GitRepository(name="grip_repo_one_clone",fs=fs,log=test_logger).git_clone(clone=self.cls_d1_bare.path, bare=False)
        d2.append_to_file(["Readme.txt"], content=FileContent("Appended text"))
        d2.git_command("commit -a -m 'appended text to readme'")
        d2.git_command_allow_stderr("push", )
        fs.cleanup()
        pass
    #f test_grip_interrogate
    def test_grip_interrogate(self) -> None:
        fs = FileSystem()
        g = GripRepoBuild(name="grip_repo_one_clone",fs=fs,log=test_logger)
        g.git_clone(clone=self.cls_g_bare.path)
        g.grip_command("configure")
        grip_root = g.grip_command("root")
        checkout_path = os.path.realpath(g.path)
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root .grip/")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root .grip/grip.toml")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root .grip")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root d1")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        fs.cleanup()
        pass
    #f test_grip_configure
    def test_grip_configure(self) -> None:
        fs = FileSystem() # "test_configure")
        g = GripRepoBuild(name="grip_repo_one_clone",fs=fs,log=test_logger)
        g.git_clone(clone=self.cls_g_bare.path)
        g.grip_command("configure")
        #print(os_command(options=g.options, cmd="cat .grip/grip.toml", cwd=g.path))
        self.assertTrue(os.path.isdir(fs.abspath(["grip_repo_one_clone"])), "git clone of bare grip repo should create grip_repo_one_clone directory")
        self.assertTrue(os.path.isdir(fs.abspath(["grip_repo_one_clone" , ".grip"])), "git clone of bare grip repo should create .grip directory")
        self.assertTrue(os.path.isdir(fs.abspath(["grip_repo_one_clone", "d1"])), "grip configure in grip repo should create d1 directory")
        #print(os_command(options=g.options, cmd="ls -lagtrR", cwd=g.path))
        fs.cleanup()
        pass
    pass
if __name__ == "__main__":
    unittest.main()
    pass
