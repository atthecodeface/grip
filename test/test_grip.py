#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, re, inspect, sys, unittest
import tempfile

from lib.oscommand import command as lib_os_command
from lib.log       import Log
from lib.options   import Options
from lib.git       import Repository as GitRepo
from types import SimpleNamespace

from typing import List, Callable, Optional, Any, ClassVar, cast
def os_command(options:Options, **kwargs:Any) -> str : return cast(str,lib_os_command(options,**kwargs))
ContentFn = Optional[Callable[...,Any]]
PathList = List[str]

grip_dir      = os.environ["GRIP_DIR"]
sys.path.append(grip_dir)

#a Test classes
#c TestLog class
class TestLog(Log):
    def __init__(self) -> None:
        Log.__init__(self)
        self.filename = "test.log"
        with open(self.filename,"w") as f: pass
        pass
    #f log_to_logfile
    def log_to_logfile(self) -> None:
        """
        Invoked to append the log to the local logfile
        """
        print("Tidying logfile")
        with open(self.filename,"a") as f:
            print("",file=f)
            print("*"*80,file=f)
            self.dump(f)
            pass
        pass
    pass
test_logger = TestLog()
test_logger.set_tidy(test_logger.log_to_logfile)

#c 'file system' class
class FileSystem(object):
    """
    A class for tests to use as a filesystem - include methods such as 'make_dir', 'create_file', and 'open'
    The class generates a temp directory which should be removed by calling 'cleanup'
    """
    path : str
    #f __init__
    def __init__(self, use_dir:Optional[str]=None) -> None:
        if use_dir is None:
            self.tmp_dir = tempfile.TemporaryDirectory(suffix=".grip_test_dir")
            self.path = self.tmp_dir.name
            pass
        else:
            self.path = use_dir
            pass
        pass
    #f cleanup
    def cleanup(self) -> None:
        if hasattr(self,"tmp_dir"):
            self.tmp_dir.cleanup()
            del(self.tmp_dir)
            del(self.path)
            pass
        pass
    #f abspath
    def abspath(self, paths:PathList) -> str:
        path = self.path
        for p in paths: path=os.path.join(path, p)
        return path
    #f make_dir
    def make_dir(self, paths:PathList, **kwargs:Any) -> None:
        path = self.abspath(paths)
        os.mkdir(path)
        pass
    #f create_file
    def create_file(self, paths:PathList, content_fn:ContentFn=None, content:Optional[str]=None) -> None:
        path = self.abspath(paths)
        with open(path,"w") as f:
            if content is not None: f.write(content)
            if content_fn is not None: f.write(content_fn())
            pass
        pass
    #f append_to_file
    def append_to_file(self, paths:PathList, content_fn:ContentFn=None, content:Optional[str]=None) -> None:
        path = self.abspath(paths)
        with open(path,"w+") as f:
            if content is not None: f.write(content)
            if content_fn is not None: f.write(content_fn())
            pass
        pass
    #f All done
    pass

#c Base loggable class
class Loggable(object):
    #f add_log_string
    def add_log_string(self, s:str) -> None:
        print(s)
        return test_logger.add_entry_string(s)
    #f log_flush
    def log_flush(self) -> None:
        return test_logger.tidy(reset=True)
    pass

#c Git repo building class
class GitRepoBuild(Loggable):
    readme_text = """
    This is a simple test git repo
    """
    #f __init__
    def __init__(self, name:str, fs:FileSystem, parent_dirs:List[str]=[], clone:Optional[str]=None, bare:bool=False, init_content_fn:ContentFn=None, branch_name:str="master") -> None:
        self.name = name
        self.path = fs.abspath(parent_dirs+[name])
        self.fs = fs
        self.options = Options()
        self.options.verbose = False
        if clone is None:
            self.fs.make_dir([self.name])
            self.git_command(cmd="init")
            if init_content_fn is not None:
                init_content_fn(self)
                pass
            else:
                self.fs.create_file([self.name,"Readme.txt"], content=self.readme_text)
                self.git_command(cmd="add Readme.txt")
                pass
            self.git_command(cmd="commit -m Init -a")
            self.git_repo = GitRepo(log=test_logger, path_str=self.path, permit_no_remote=True)
            pass
        else:
            self.git_repo = GitRepo.clone(log=test_logger, options=self.options, repo_url=clone, dest=self.path, bare=bare, new_branch_name=branch_name)
            if not bare:
                upstream =self.git_repo.get_upstream()
                if upstream is not None: self.git_repo.set_upstream_of_branch(branch_name, upstream)
            pass
        pass
    #f bare_clone
    def bare_clone(self) -> 'GitRepoBuild':
        return  self.__class__("%s.git"%(self.name),self.fs, clone=self.path, bare=True)
    #f make_dir
    def make_dir(self, paths:PathList, **kwargs:Any) -> None:
        self.add_log_string("Making directory %s"%str([self.name]+paths))
        self.fs.make_dir([self.name]+paths, **kwargs)
        pass
    #f create_file
    def create_file(self, paths:PathList, **kwargs:Any) -> None:
        self.add_log_string("Creating file %s"%str([self.name]+paths))
        self.fs.create_file([self.name]+paths, **kwargs)
        pass
    #f append_to_file
    def append_to_file(self, paths:PathList, **kwargs:Any) -> None:
        self.add_log_string("Appending to file %s"%str([self.name]+paths))
        self.fs.append_to_file([self.name]+paths, **kwargs)
        pass
    #f git_command
    def git_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        cwd = self.path
        if wd is not None: cwd = os.path.join(self.path, wd)
        self.add_log_string("Test running git command in wd '%s' of '%s'"%(cwd, cmd))
        return os_command(self.options, cmd="git %s"%cmd, cwd=cwd, log=test_logger, **kwargs)
    #f git_command_allow_stderr
    def git_command_allow_stderr(self, cmd:str, **kwargs:Any) -> str:
        return self.git_command(cmd=cmd, stderr_output_indicates_error=False, **kwargs)
    pass

#c Grip repo building class
class GripRepoBuild(GitRepoBuild):
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
    def __init__(self, name:str, fs:FileSystem, **kwargs:Any) -> None:
        global grip_dir
        GitRepoBuild.__init__(self, name, fs, init_content_fn=self.init_content, **kwargs)
        self.grip_exec = "%s/grip"%(grip_dir)
        pass
    #f init_content
    def init_content(self, git_repo:GitRepoBuild) -> None:
        git_repo.make_dir([".grip"])
        git_repo.create_file([".grip","grip.toml"], content=self.grip_toml.format(fs_path=self.fs.path))
        git_repo.git_command(wd=".grip", cmd="add grip.toml")
        pass
    #f grip_command
    def grip_command(self, cmd:str, wd:Optional[str]=None, **kwargs:Any) -> str:
        cwd = self.path
        if wd is not None: cwd = os.path.join(self.path, wd)
        self.add_log_string("Test running grip command in wd '%s' of '%s'"%(cwd, cmd))
        return os_command(options=self.options,
                          cmd="%s --show-log --verbose %s"%(self.grip_exec, cmd),
                          cwd=cwd,
                          **kwargs)

        pass
    pass

#c Basic grip test case
class Test(unittest.TestCase):
    #v class properties
    cls_fs : ClassVar[FileSystem]
    cls_d1      : ClassVar[GitRepoBuild]
    cls_d1_bare : ClassVar[GitRepoBuild]
    cls_d2      : ClassVar[GitRepoBuild]
    cls_d2_bare : ClassVar[GitRepoBuild]
    cls_g       : ClassVar[GripRepoBuild]
    cls_g_bare  : ClassVar[GitRepoBuild]
    #v setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        try:
            fs = FileSystem()
            cls.cls_fs = fs
            cls.cls_d1       = GitRepoBuild("d_1",fs,[])
            cls.cls_d1_bare  = cls.cls_d1.bare_clone()
            cls.cls_d2       = GitRepoBuild("d_2",fs,[])
            cls.cls_d2_bare  = cls.cls_d2.bare_clone()
            cls.cls_g       = GripRepoBuild("grip_1",fs)
            cls.cls_g_bare  = cls.cls_g.bare_clone()
        except:
            test_logger.tidy()
            raise
        pass
    #v tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.cls_fs.cleanup()
        except:
            test_logger.tidy()
            raise
        test_logger.tidy()
        pass
    #f test_git_clone
    def test_git_clone(self) -> None:
        fs = FileSystem()
        d2 = GitRepoBuild("grip_repo_one_clone",fs,clone=self.cls_d1_bare.path)
        d2.append_to_file(["Readme.txt"], content="Appended text")
        d2.git_command("commit -a -m 'appended text to readme'")
        d2.git_command_allow_stderr("push", )
        fs.cleanup()
        pass
    #f test_grip_interrogate
    def test_grip_interrogate(self) -> None:
        fs = FileSystem()
        g = GripRepoBuild("grip_repo_one_clone",fs,clone=self.cls_g_bare.path)
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
        g = GripRepoBuild("grip_repo_one_clone",fs,clone=self.cls_g_bare.path)
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
