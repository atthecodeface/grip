#a Imports
import os
from pathlib import Path

from .test_lib.filesystem import FileSystem, FileContent
from .test_lib.loggable import TestLog
from .test_lib.unittest import TestCase
from .test_lib.git import Repository as GitRepository
from .test_lib.git import RepoBuildContentFn
from .test_lib.grip import Repository as GripRepository
from .test_lib.grip import GripToml
from .test_lib.toml_file import Toml

from typing import Type, List, Optional, Any, ClassVar, Dict

#a Grip repositories for tests
class D3Toml(Toml):
    doc="subrepo d3"
    env = {"SRC":"@GRIP_REPO_PATH@", "OVERRIDE_ME":"bad value"}
    clean_sim = {"wd":"@SRC@", "exec":"clean_sim d3"}
    show_env = {
        "env":{"SRC_ROOT":"@GRIP_REPO_PATH@",
               "BUILD_ROOT":"@BUILD_DIR@",
               "MAKE_OPTIONS":"@GRIP_REPO_PATH@/Makefile D3_SRC_ROOT=@SRC_ROOT@ BUILD_ROOT=@BUILD_DIR@"},
        "exec":"echo BUILD_DIR=@BUILD_DIR@ D3_SRC_ROOT=@SRC_ROOT@ BUILD_ROOT=@BUILD_ROOT@ MAKE_OPTIONS=@MAKE_OPTIONS@ D3_SRC_ROOT=$${SRC_ROOT} BUILD_ROOT=$${BUILD_ROOT} MAKE_OPTIONS=$${MAKE_OPTIONS}"}
    run_sim = {"exec":"run_sim d3", "action":"yes"}
    pass

class D4Toml(Toml):
    doc="subrepo d4"
    env = {"SRC":"@GRIP_REPO_PATH@"}
    circle = {"env":{"D4_THING1":"@D4_THING2@", "D4_THING2":"@D4_THING1@"}}
    show_env = {"exec":"echo GRIP_ROOT_PATH=@GRIP_ROOT_PATH@ GRIP_ROOT_PATH=${GRIP_ROOT_PATH} D4_SRC_ROOT=@SRC@ NOT_D4_SRC_ROOT=${SRC} NOT_GRIP_ROOT_PATH=$${GRIP_ROOT_PATH}", }
    pass

class ExampleConfig1Toml(Toml):
    repos = ["d2"]
    d2 = {"install": {"requires":[], "wd":"", "exec":"do_exec"}}
    pass

class ExampleConfig2Toml(Toml):
    repos = ["d2", "d3"]
    pass

class ExampleConfig3Toml(Toml):
    repos = ["d2", "d3", "d4"]
    pass

class BaseGripToml(GripToml):
    name            = "test_grip"
    default_config  = "cfg0"
    doc             = "Use of local environment for repo path"
    configs         : List[str] = []
    base_repos      : List[str] = []
    workflow        = "readonly"
    stages          = ["install"]
    env             : Dict[str,str] = {}
    config : Dict[str,Any] = {}
    repo   : Dict[str,Any] = {}
    pass

class ExampleToml(BaseGripToml):
    doc             = "Use of local environment for repo path"
    configs         = ["cfg0","cfg1"]
    base_repos      = ["d1"]
    stages          = ["show_env"]
    workflow        = "readonly"
    env             = {"D2ENV":"d2"}
    logging         = "True"
    config = {"cfg1":ExampleConfig1Toml()}
    repo   : Dict[str,Any] = {}
    def __init__(self, fs:FileSystem, **kwargs:Any):
        self.repo["d1"] = { "url":"%s/d_1.git" % fs.path, "branch":"master", "path":"d1" }
        self.repo["d2"] = { "url":"%s/d_2.git" % fs.path, "branch":"master", "path":"@D2ENV@" }
        Toml.__init__(self, **kwargs)
        pass
    pass

class GripTomlEnv1(BaseGripToml):
    name            = "grip_toml_env_1"
    configs         = ["cfg0", "cfg1"]
    env             = {"FS_PATH":"@FS_PATH@", "THING1":"@FS_PATH@", "THING2":"@THING1@"}
    config = {"cfg1":ExampleConfig1Toml()}
    repo : Dict[str,Any] = {}
    repo["d1"] = {"url":'@FS_PATH@/d_1.git',"path":'d1'}
    repo["d2"] = {"url":'@LOCAL_FS_PATH@/d_2.git',"path":'d2', "env":{"LOCAL_FS_PATH":"@FS_PATH@"}}
    pass

class GripTomlEnvFull(BaseGripToml):
    name            = "grip_toml_env_1"
    configs         = ["cfg0", "cfg1", "cfg2", "cfg3"]
    stages          = ["show_env"]
    env             = {"FS_PATH":"@FS_PATH@",
                       "BUILD_DIR":"@GRIP_ROOT_PATH@/build",
                       "THING1":"@FS_PATH@",
                       "THING2":"@THING1@",}
    config = {"cfg1":ExampleConfig1Toml(),
              "cfg2":ExampleConfig2Toml(),
              "cfg3":ExampleConfig3Toml(),
    }
    repo : Dict[str,Any] = {}
    repo["d1"] = {"url":'@FS_PATH@/d_1.git',"path":'d1'}
    repo["d2"] = {"url":'@FS_PATH@/d_2.git',"path":'d2', "env":{"LOCAL_FS_PATH":"@FS_PATH@"}}
    repo["d3"] = {"url":'@FS_PATH@/d_3.git',"path":'d3',"env":{"OVERRIDE_ME":"d3 has been overridden"}}
    repo["d4"] = {"url":'@FS_PATH@/d_4.git',"path":'d4'}
    pass

class GripTomlEnvCirc1(GripTomlEnv1):
    env             = {"FS_PATH":"@FS_PATH@", "THING1":"@THING2@", "THING2":"@THING1@"}
    pass

class GripTomlEnvCirc2(GripTomlEnv1):
    env             = {"FS_PATH":"@FS_PATH@"}
    repo = dict(GripTomlEnv1.repo.items())
    repo["d2"] = {"url":'@FS_PATH@/d_2.git',"path":'d2',"env":{"D2_THING1":"@D2_THING2@", "D2_THING2":"@D2_THING1@"}}
    pass

#c ExampleRepository - base repository with d_1 and d_2, config cfg1 of ExampleConfig1Toml
class ExampleRepository(GripRepository):
    grip_toml_class = ExampleToml
    pass

#c EnvRepository - repository with d_1 only, path of d1, needing FS_PATH environment, config cfg0 plain
class EnvRepository(GripRepository):
    grip_toml_class = GripTomlEnv1
    pass

#c EnvFullRepository - repository with d1, d2, d3 and d4, needing FS_PATH environment, config cfg0/1/2/3
class EnvFullRepository(GripRepository):
    grip_toml_class = GripTomlEnvFull
    pass

#c EnvCirc1Repository - repository with d_1 only, path of d1, but circular environment in grip.toml base environment
class EnvCirc1Repository(GripRepository):
    grip_toml_class = GripTomlEnvCirc1
    pass

#c EnvCirc2Repository - repository with d_1 only, path of d1, but circular environment in grip.toml repo d1 environment
class EnvCirc2Repository(GripRepository):
    grip_toml_class = GripTomlEnvCirc2
    pass

#a Test classes
#c RepoPair
class RepoPair(object):
    def __init__(self, name:str, cls:Type[GitRepository], fs:FileSystem, log:TestLog, init_content:Optional[RepoBuildContentFn]=None):
        self.init_repo = cls(name=name, fs=fs, parent_dirs=[], log=log)
        self.init_repo.git_init(init_content)
        self.bare_repo = self.init_repo.bare_clone()
        pass
    def bare(self) -> GitRepository: return self.bare_repo
    pass
#c Basic grip test case
class BasicTest(TestCase):
    #v class properties
    cls_fs      : ClassVar[FileSystem]
    cls_d1      : ClassVar[RepoPair]
    cls_d2      : ClassVar[RepoPair]
    cls_d3      : ClassVar[RepoPair]
    cls_d4      : ClassVar[RepoPair]
    cls_grip_base      : ClassVar[RepoPair]
    cls_grip_env       : ClassVar[RepoPair]
    cls_grip_env_full  : ClassVar[RepoPair]
    cls_grip_env_circ1 : ClassVar[RepoPair]
    cls_grip_env_circ2 : ClassVar[RepoPair]
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        TestCase.setUpSubClass(cls)
        try:
            fs = FileSystem(cls._logger)
            cls.cls_fs  = fs
            cls.cls_d1  = RepoPair(name="d_1",cls=GitRepository,fs=fs,log=cls._logger, init_content=GitRepository.add_readme)
            cls.cls_d2  = RepoPair(name="d_2",cls=GitRepository,fs=fs,log=cls._logger, init_content=GitRepository.add_readme)
            cls.cls_d3  = RepoPair(name="d_3",cls=GitRepository,fs=fs,log=cls._logger, init_content=GitRepository.add_toml(D3Toml(),"grip.toml"))
            cls.cls_d4  = RepoPair(name="d_4",cls=GitRepository,fs=fs,log=cls._logger, init_content=GitRepository.add_toml(D4Toml(),"grip.toml"))
            cls.cls_grip_base      = RepoPair(name="grip_1",       cls=ExampleRepository,fs=fs,log=cls._logger)
            cls.cls_grip_env       = RepoPair(name="grip_env",     cls=EnvRepository,fs=fs,log=cls._logger)
            cls.cls_grip_env_full  = RepoPair(name="grip_env_full", cls=EnvFullRepository,fs=fs,log=cls._logger)
            cls.cls_grip_env_circ1 = RepoPair(name="grip_env_circ1",cls=EnvCirc1Repository,fs=fs,log=cls._logger)
            cls.cls_grip_env_circ2 = RepoPair(name="grip_env_circ2",cls=EnvCirc2Repository,fs=fs,log=cls._logger)
        except:
            cls._logger.tidy()
            raise
        cls._logger.tidy()
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.cls_fs.cleanup()
        except:
            TestCase.tearDownSubClass(cls)
            raise
        TestCase.tearDownSubClass(cls)
        pass
    #f test_git_clone
    def test_git_clone(self) -> None:
        fs = FileSystem(log=self._logger)
        d2 = GitRepository(name="grip_repo_one_clone",fs=fs,log=self._logger).git_clone(clone=self.cls_d1.bare().abspath, bare=False)
        d2.append_to_file(Path("Readme.txt"), content=FileContent("Appended text"))
        d2.git_command("commit -a -m 'appended text to readme'")
        d2.git_command_allow_stderr("push", )
        fs.cleanup()
        pass
    #f test_grip_environment
    def test_grip_environment(self) -> None:
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="g",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_env.bare().abspath)
        env = {"FS_PATH":str(self.cls_fs.path)}
        doc_cmd = g.grip_command_full_result("doc")
        self.assertEqual(doc_cmd.rc(),1,"Grip doc should not have an error for undefined environment variables on an unconfigured repo")
        self.assertRegex(doc_cmd.stderr(),r"Environment error","Grip doc should have stderr output for undefined environment variables on an unconfigured repo")
        doc_cmd = g.grip_command_full_result("doc", env=env)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for defined environment variables")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        cfg_cmd = g.grip_command_full_result("configure")
        self.assertEqual(cfg_cmd.rc(),4,"Grip configure should return an error for undefined environment variables")
        self.assertRegex(cfg_cmd.stderr(),r"Environment error","Grip configure should have stderr output for undefined environment variables on an unconfigured repo")

        cfg_cmd = g.grip_command_full_result("configure", env=env)
        self.assertEqual(cfg_cmd.rc(),0,"Grip configure should complete successfully if environment is provided (stderr %s)"%(cfg_cmd.stderr()))
        
        fs.cleanup()
        pass
    #f test_grip_environment_full_cfg2
    def test_grip_environment_full_cfg2(self) -> None:
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="g",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_env_full.bare().abspath)
        env = {"FS_PATH":str(self.cls_fs.path)}
        doc_cmd = g.grip_command_full_result("doc")
        self.assertEqual(doc_cmd.rc(),1,"Grip doc should have an error for undefined environment variables on an unconfigured repo")
        self.assertRegex(doc_cmd.stderr(),r"Environment error","Grip doc should have stderr output for undefined environment variables on an unconfigured repo")
        doc_cmd = g.grip_command_full_result("doc", env=env)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for defined environment variables")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        cfg_cmd = g.grip_command_full_result("configure")
        self.assertEqual(cfg_cmd.rc(),4,"Grip configure should return an error for undefined environment variables")
        self.assertRegex(cfg_cmd.stderr(),r"Environment error","Grip configure should have stderr output for undefined environment variables on an unconfigured repo")

        cfg_cmd = g.grip_command_full_result("configure cfg2", env=env)
        self.assertEqual(cfg_cmd.rc(),0,"Grip configure should complete successfully if environment is provided (stderr %s)"%(cfg_cmd.stderr()))
        
        doc_cmd = g.grip_command_full_result("doc")
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for defined environment variables")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        fs.cleanup()
        pass
    #f test_grip_environment_full_cfg3
    def test_grip_environment_full_cfg3(self) -> None:
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="g",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_env_full.bare().abspath)
        env = {"FS_PATH":str(self.cls_fs.path)}
        env_break_circle = {"D4_THING1":"thing1"}
        env_both = {"FS_PATH":str(self.cls_fs.path), "D4_THING1":"thing1"}
        doc_cmd = g.grip_command_full_result("doc")
        self.assertEqual(doc_cmd.rc(),1,"Grip doc should have an error for undefined environment variables on an unconfigured repo")
        self.assertRegex(doc_cmd.stderr(),r"Environment error","Grip doc should have stderr output for undefined environment variables on an unconfigured repo")
        doc_cmd = g.grip_command_full_result("doc", env=env)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for defined environment variables")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        cfg_cmd = g.grip_command_full_result("configure")
        self.assertEqual(cfg_cmd.rc(),4,"Grip configure should return an error for undefined environment variables")
        self.assertRegex(cfg_cmd.stderr(),r"Environment error","Grip configure should have stderr output for undefined environment variables on an unconfigured repo")

        cfg_cmd = g.grip_command_full_result("configure cfg3", env=env)
        self.assertEqual(cfg_cmd.rc(),4,"Grip configure of cfg3 should fail after cloning of d4 (stderr %s)"%(cfg_cmd.stderr()))
        # It has cloned the repos...
        cfg_cmd = g.grip_command_full_result("reconfigure", env=env_both)
        self.assertEqual(cfg_cmd.rc(),0,"Grip configure should complete successfully if environment is provided (stderr %s)"%(cfg_cmd.stderr()))

        # That should have written out the environment - but not for the local circles
        doc_cmd = g.grip_command_full_result("doc")
        self.assertEqual(doc_cmd.rc(),1,"Grip doc should not have an error for defined environment variables")
        self.assertRegex(doc_cmd.stderr(),r"Environment error","Grip doc should have stderr output for undefined environment variables")

        doc_cmd = g.grip_command_full_result("doc", env=env_break_circle)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for defined environment variables")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        fs.cleanup()
        pass
    #f test_grip_environment_circular1
    def test_grip_environment_circular1(self) -> None:
        """
        grip_env_circ1 has a circular dependency in the main env of grip.toml
        """
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="g",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_env_circ1.bare().abspath)
        env = {"FS_PATH":str(self.cls_fs.path)}
        env_break_circle = {"FS_PATH":str(self.cls_fs.path), "THING1":"thing1"}
        doc_cmd = g.grip_command_full_result("doc", env=env)
        self.assertEqual(doc_cmd.rc(),1,"Grip doc should have return code 1 for undefined environment variables on an unconfigured repo")
        self.assertRegex(doc_cmd.stderr(),r"Circular environment dependency","Grip doc should have circular dependency error")
        cfg_cmd = g.grip_command_full_result("configure", env=env)
        self.assertEqual(cfg_cmd.rc(),4,"Grip configure should return an error for circularly-dependent environment variables")
        self.assertRegex(cfg_cmd.stderr(),r"Circular environment dependency","Grip configure should have circular dependency error")

        doc_cmd = g.grip_command_full_result("doc", env=env_break_circle)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for a circular dependency that is broken by supplying an external value")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        fs.cleanup()
        pass
    #f test_grip_environment_circular2
    def test_grip_environment_circular2(self) -> None:
        """
        grip_env_circ2 has a circular dependency in the repo 'd2' env of grip.toml - so important for configuring with that repo cfg1 only
        """
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="g",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_env_circ2.bare().abspath)
        env = {"FS_PATH":str(self.cls_fs.path)}
        env_break_circle = {"FS_PATH":str(self.cls_fs.path), "D2_THING1":"thing1"}
        doc_cmd = g.grip_command_full_result("doc", env=env)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have return code 0 for undefined environment variables on an unconfigured repo")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output for unconfigured repo")
        cfg_cmd = g.grip_command_full_result("configure cfg1", env=env)
        self.assertNotEqual(cfg_cmd.rc(),0,"Grip configure should return an error for circularly-dependent environment variables")
        self.assertRegex(cfg_cmd.stderr(),r"Circular environment dependency","Grip configure should have circular dependency error")

        doc_cmd = g.grip_command_full_result("doc", env=env_break_circle)
        self.assertEqual(doc_cmd.rc(),0,"Grip doc should not have an error for undefined environment variables on an unconfigured repo")
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip doc should have no stderr output")

        fs.cleanup()
        pass
    #f test_grip_environment_show_env
    def test_grip_environment_show_env(self) -> None:
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="g",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_env_full.bare().abspath)
        env = {"FS_PATH":str(self.cls_fs.path), "D4_THING1":"thing1"}
        cfg_cmd = g.grip_command_full_result("configure cfg3", env=env)
        self.assertEqual(cfg_cmd.rc(),0,"Grip configure should complete successfully if environment is provided (stderr %s)"%(cfg_cmd.stderr()))

        # That should have written out the environment - but not for the local circles
        doc_cmd = g.grip_command_full_result("make show_env", env=env)
        self.assertEqual(doc_cmd.stderr().strip(),"","Grip make show env should have no error output (%s)"%doc_cmd.stderr())
        self.assertEqual(doc_cmd.rc(),0,"Grip make show env should not have an error")
        env_vars = doc_cmd.stdout().strip().split()
        # print(doc_cmd.stdout())
        make_env_vars = {}
        make_env_vars["BUILD_DIR"]    = "%s/build"%(str(g.abspath))
        make_env_vars["D3_SRC_ROOT"]  = "%s/d3"%(str(g.abspath))
        make_env_vars["D4_SRC_ROOT"]  = "%s/d4"%(str(g.abspath))
        make_env_vars["MAKE_OPTIONS"] = "%s/d3/Makefile"%(str(g.abspath))
        make_env_vars["GRIP_ROOT_PATH"] = "%s"%(str(g.abspath))
        count = 0
        for ev in env_vars:
            nv = ev.split("=")
            if len(nv)<2: continue
            (n,v)=nv
            if n in make_env_vars:
                self.assertEqual(v,make_env_vars[n],"Output of make show_env mismatched for '%s'"%n)
                count += 1
                pass
            pass
        self.assertEqual(count,9,"Output of make show_env had incorrect known values")
        fs.cleanup()
        pass
    #f test_grip_interrogate
    def test_grip_interrogate(self) -> None:
        fs = FileSystem(log=self._logger)
        g = GripRepository(name="grip_repo_one_clone",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_base.bare().abspath)
        g.grip_command("configure")
        grip_root = g.grip_command("root")
        checkout_path = os.path.realpath(g.abspath)
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root --grip-path .grip/")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root --grip-path .grip/grip.toml")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root --grip-path .grip")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root --grip-path d1")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        fs.cleanup()
        pass
    #f test_grip_configure
    def test_grip_configure(self) -> None:
        fs = FileSystem(log=self._logger) # "test_configure")
        g = GripRepository(name="grip_repo_one_clone",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_grip_base.bare().abspath)
        g.grip_command("configure")
        fs.log_hashes(reason="post grip configure", path=Path("grip_repo_one_clone/.grip"), glob="*", depth=-1, use_full_name=False)
        g.log_file_contents(fs.abspath(Path("grip_repo_one_clone/.grip/local.log")),prefix="%%log%% ")
        #print(os_command(options=g.options, cmd="cat .grip/grip.toml", cwd=g.path))
        self.assertTrue(fs.abspath(Path("grip_repo_one_clone")).is_dir()        , "git clone of bare grip repo should create grip_repo_one_clone directory")
        self.assertTrue(fs.abspath(Path("grip_repo_one_clone/.grip")).is_dir()  , "git clone of bare grip repo should create .grip directory")
        self.assertTrue(fs.abspath(Path("grip_repo_one_clone/d1")).is_dir()     , "grip configure in grip repo should create d1 directory")
        #print(os_command(options=g.options, cmd="ls -lagtrR", cwd=g.path))
        fs.cleanup()
        pass
    pass
#a Toplevel
#f Create tests
test_suite = [BasicTest]
