#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Imports
import os, re, inspect, sys, unittest
import tempfile

grip_test_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
grip_dir      = os.path.dirname(grip_test_dir)
sys.path.append(grip_dir)

from lib.git       import GitRepo, git_command
from lib.oscommand import command as os_command
from types import SimpleNamespace
#a Test classes
#c 'file system' class
class FileSystem(object):
    """
    A class for tests to use as a filesystem - include methods such as 'make_dir', 'create_file', and 'open'
    The class generates a temp directory which should be removed by calling 'cleanup'
    """
    tmp_dir = None
    #f __init__
    def __init__(self):
        self.tmp_dir = tempfile.TemporaryDirectory(suffix=".grip_test_dir")
        self.path = self.tmp_dir.name
        pass
    #f cleanup
    def cleanup(self):
        if self.tmp_dir is not None:
            self.tmp_dir.cleanup()
            self.tmp_dir = None
            self.path = None
            pass
        pass
    #f abspath
    def abspath(self, paths):
        path = self.path
        for p in paths: path=os.path.join(path, p)
        return path
    #f make_dir
    def make_dir(self, paths):
        path = self.abspath(paths)
        os.mkdir(path)
        pass
    #f create_file
    def create_file(self, paths, content_fn=None, content=None):
        path = self.abspath(paths)
        with open(path,"w") as f:
            if content is not None: f.write(content)
            if content_fn is not None: f.write(content_fn())
            pass
        pass
    #f append_to_file
    def append_to_file(self, paths, content_fn=None, content=None):
        path = self.abspath(paths)
        with open(path,"w+") as f:
            if content is not None: f.write(content)
            if content_fn is not None: f.write(content_fn())
            pass
        pass
    #f All done
    pass

#c Git repo building class
class GitRepoBuild(object):
    readme_text = """
    This is a simple test git repo
    """
    #f __init__
    def __init__(self, name, fs, parent_dirs=[], clone=None, bare=False, init_content_fn=None):
        self.name = name
        self.path = fs.abspath(parent_dirs+[name])
        self.fs = fs
        self.options = SimpleNamespace()
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
            self.git_repo = GitRepo(path=self.path, permit_no_remote=True)
            pass
        else:
            self.git_repo = GitRepo.clone(self.options,repo_url=clone,dest=self.path, bare=bare)
            pass
        pass
    #f bare_clone
    def bare_clone(self):
        return  self.__class__("%s.git"%(self.name),self.fs, clone=self.path, bare=True)
    #f make_dir
    def make_dir(self, paths, *args, **kwargs):
        print("Making directory %s"%str([self.name]+paths))
        self.fs.make_dir([self.name]+paths, *args, **kwargs)
        pass
    #f create_file
    def create_file(self, paths, *args, **kwargs):
        print("Creating file %s"%str([self.name]+paths))
        self.fs.create_file([self.name]+paths, *args, **kwargs)
        pass
    #f append_to_file
    def append_to_file(self, paths, *args, **kwargs):
        print("Appending to file %s"%str([self.name]+paths))
        self.fs.append_to_file([self.name]+paths, *args, **kwargs)
        pass
    #f git_command
    def git_command(self, cmd, wd=None, **kwargs):
        cwd = self.path
        if wd is not None: cwd = os.path.join(self.path, wd)
        print("Test running git command in wd '%s' of '%s'"%(cwd, cmd))
        return git_command(self.options, cmd=cmd, cwd=cwd, **kwargs)
    #f git_command_allow_stderr
    def git_command_allow_stderr(self, cmd, **kwargs):
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
    def __init__(self, name, fs, **kwargs):
        global grip_dir
        GitRepoBuild.__init__(self, name, fs, init_content_fn=self.init_content, **kwargs)
        self.grip_exec = "%s/grip"%(grip_dir)
        pass
    #f init_content
    def init_content(self, git_repo):
        git_repo.make_dir([".grip"])
        git_repo.create_file([".grip","grip.toml"], content=self.grip_toml.format(fs_path=self.fs.path))
        git_repo.git_command(wd=".grip", cmd="add grip.toml")
        pass
    #f grip_command
    def grip_command(self, cmd, wd=None, **kwargs):
        cwd = self.path
        if wd is not None: cwd = os.path.join(self.path, wd)
        print("Test running grip command in wd '%s' of '%s'"%(cwd, cmd))
        return os_command(options=self.options,
                          cmd="%s %s"%(self.grip_exec, cmd),
                          cwd=cwd,
                          **kwargs)
        
        pass
    pass

#c Basic gript test case
class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fs = FileSystem()
        cls.cls_fs = fs
        cls.cls_d1       = GitRepoBuild("d_1",fs,[])
        cls.cls_d1_bare  = cls.cls_d1.bare_clone()
        cls.cls_d2       = GitRepoBuild("d_2",fs,[])
        cls.cls_d2_bare  = cls.cls_d2.bare_clone()
        cls.cls_g       = GripRepoBuild("grip_1",fs)
        cls.cls_g_bare  = cls.cls_g.bare_clone()
        pass
    @classmethod
    def tearDownClass(cls):
        cls.cls_fs.cleanup()
        pass
    def test_git_clone(self):
        fs = FileSystem()
        d2 = GitRepoBuild("grip_repo_one_clone",fs,clone=self.cls_d1_bare.path)
        d2.append_to_file(["Readme.txt"], content="Appended text")
        d2.git_command("commit -a -m 'appended text to readme'")
        d2.git_command_allow_stderr("push", )
        fs.cleanup()
        pass
    def test_grip_interrogate(self):
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
    def test_grip_configure(self):
        fs = FileSystem()
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
