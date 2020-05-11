#a Imports
from pathlib import Path

from typing import Optional, Dict, Sequence, Collection, Any, Union, Type
from lib.exceptions import *
from lib.base       import GripBase
from lib.tomldict import TomlDict, TomlDictParser
from lib.exceptions import *
from lib.env import GripEnv, EnvTomlDict
from lib.descriptor.stage import Dependency as StageDependency
from lib.descriptor.stage import Descriptor as StageDescriptor
from lib.descriptor.stage import StageTomlDict
from lib.descriptor.repo  import RepoDescTomlDict
from lib.descriptor.grip import Descriptor as GripDescriptor
from lib.configstate.grip import GripConfigStateInitial    as GripRepositoryInitial
from lib.configstate.grip import GripConfigStateConfigured as GripRepositoryConfigured

from .test_lib.grip import GripBaseTest
from .test_lib.loggable import Loggable
from .test_lib.unittest import UnitTestObject, AKV
from .test_lib.unittest import TestCase
from .test_lib.toml_file import Toml

from typing import Dict, List, Any, Optional, Union, cast

#a Unittest for GripRepository class
#c DefaultConfigToml
class DefaultConfigToml(Toml):
    name="y"
    workflow="single"
    default_config="x"
    configs=["x"]
    base_repos:List[str]=[]
    repo:Dict[str,Any]={}
    pass

#c TestBase
Asserts = Dict[str, Any]
SubrepoTomls = Dict[str,Type[Toml]]
class TestBase(object):
    class ConfigToml(DefaultConfigToml):pass
    subrepos    : SubrepoTomls = {}
    config_name : Union [None, bool, str] = False
    grd_assert  : Asserts = {}
    cfg_assert  : Asserts = {}
    exception_expected : Optional[Type[Exception]]= None
#c TestSet
class TestSet(UnitTestObject, Loggable):
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        TestCase.setUpSubClass(cls)
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        TestCase.tearDownSubClass(cls)
        pass
    #f debug_repo_desc
    def debug_repo_desc(self, repo_desc:GripDescriptor) -> None:
        def p(acc:Any, s:str, indent:int=0) -> Any:
            self._logger.add_log_string("grd: " + ("  "*indent)+s)
        repo_desc.prettyprint("",p)
        pass
    def do_read_toml(self) -> None:
        self.grip_initial.read_desc_state()
        # .d.read_toml_file(grip_toml_path=Path("grip.toml"), subrepo_descs=[])
        # self.grd.build_from_toml_dict()
        # self.grd.validate()
        # self.grd.resolve()
        # self.grd.resolve_git_urls(self.base.git_repo.get_git_url())
        # self.grd  = self.grip.initial_repo_desc
        pass
    def _test_it(self, test:Type[TestBase]) -> None:
        self.test = test
        self.config_toml = test.ConfigToml()._as_string()
        self.local_config_toml = """config="y"\ngrip_git_url="test"\nbranch=""\n"""
        files = {}
        files[".grip/grip.toml"]=self.config_toml
        files[".grip/local.config.toml"]=self.local_config_toml
        for (sn,st) in self.test.subrepos.items():
            files["%s/grip.toml"%sn] = st()._as_string()
            pass
        self._logger.add_log_string("Test %s"%test.__qualname__)
        self._logger.add_log_string("Config %s"%self.test.config_name)
        self._logger.add_log_string("Toml %s"%self.config_toml)
        self.base  = GripBaseTest(log=self._logger, files=files)
        self.grip_initial = GripRepositoryInitial(base=self.base)
        if self.test.exception_expected is not None:
            self._logger.add_log_string("Checking exception is raised by reading Toml")
            self.assertRaises(self.test.exception_expected, self.do_read_toml)
            return
        else:
            self._logger.add_log_string("Reading Toml")
            self.do_read_toml()
            self.debug_repo_desc(self.grip_initial.initial_repo_desc)
            pass
        if len(self.test.grd_assert)>0:
            self._logger.add_log_string("Checking resultant grd against descriptor")
            self._test_obj_asserts(self.grip_initial.initial_repo_desc, self.test.grd_assert, "grip_repo_desc")
            pass
        if self.test.config_name is not False:
            self._logger.add_log_string("Selecting configuration %s"%self.test.config_name)
            config_name = cast(Optional[str],self.test.config_name)
            try:
                config_name = self.grip_initial.select_configuration(config_name)
                pass
            except Exception as e:
                self._logger.add_log_string("No config selected - ensuring this is what test requires")
                self._logger.add_log_string(str(e))
                self._logger.add_log_string(str(self.test.cfg_assert))
                self.assertTrue(len(self.test.cfg_assert)==0)
                return
                pass
            if config_name is not None:
                self.grip_configured = GripRepositoryConfigured(self.grip_initial)
                self.grip_configured.read_desc()
                self.debug_repo_desc(self.grip_configured.full_repo_desc)
                cfg = self.grip_configured.config_desc
                self._logger.add_log_string("Checking resultant cfg against descriptor")
                self._test_obj_asserts(cfg, self.test.cfg_assert, "config_desc")
                pass
            pass
        pass
    #f _create_test_fns_of_class
    @classmethod
    def _create_test_fns_of_class(cls, test_cls:Type['TestBase'])->None:
        for t in test_cls.__subclasses__():
            def f(self:'TestSet',t:Type['TestBase']=t) -> None:
                self._test_it(test=t)
                self._logger.add_log_string("Reached end of test successfully - a Pass")
            setattr(cls, "test_%s"%(t.__qualname__), f)
            pass
        pass

    #f All done
    pass

#c TestUnconfigured
class TestUnconfigured(TestSet):
    """
        Note that only configuration's repodescs have resolved git_url properties
    """
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        TestCase.setUpSubClass(cls)
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        TestCase.tearDownSubClass(cls)
        pass
    class Test(TestBase):
        class ConfigToml(DefaultConfigToml): pass
        grd_assert = {"name":"y","default_config":"x", "base_repos":[]}
        pass
    class WorkingTest(Test):
        pass
    class BadDefaultConfig(Test):
        class ConfigToml(DefaultConfigToml): default_config = "<not a defined config>"
        exception_expected = GripTomlError
        pass
    class WorkflowSingle(Test):
        class ConfigToml(DefaultConfigToml): workflow="single"
        pass
    class WorkflowReadOnly(Test):
        class ConfigToml(DefaultConfigToml): workflow="readonly"
        pass
    class BadWorkflow(Test):
        class ConfigToml(DefaultConfigToml): workflow="unknown_workflow"
        exception_expected = RepoDescError
        pass
    class RepoUnparsedKey(Test):
        class ConfigToml(DefaultConfigToml):
            this_is_a_bad_key="a"
            pass
        exception_expected = TomlError
        pass
    class RepoUrl(Test):
        class ConfigToml(DefaultConfigToml):
            base_repos=["fred"]
            repo={"fred":{"url":'a',"path":'b'}}
            pass
        grd_assert:Any = {"base_repos":["fred"],
                      "repos":{
                          "fred":{"name":"fred"}, # Repo is not resolved until configured so url and path are not valid
                      }}
        pass
    class EmptyBaseRepos(Test):
        class ConfigToml(DefaultConfigToml):
            base_repos : List[str] =[]
            repo={"fred":{"url":'a',"path":'b'}}
            pass
        grd_assert : Any = {"base_repos":[],
                            "repos":{"fred":{},}}
        pass
    class BadBaseRepos(Test):
        class ConfigToml(DefaultConfigToml):
            base_repos=["tom"]
            repo={"fred":{"url":'a',"path":'b'}}
            pass
        exception_expected = RepoDescError
        pass
    pass

#c TestConfigured
class TestConfigured(TestSet):
    """
    Repos should be defined including url and path
    """
    class Test(TestBase):
        class ConfigToml(Toml):
            name="y"
            workflow="readonly"
            default_config="x"
            configs=["x","y"]
            base_repos=["fred"]
            repo:Dict[str,Any]={}
            repo={"fred":{"url":'ssh://me@there/path/to/thing.git'},
                  "jim":{"url":'some/path/to/jim.git',"workflow":"single"},
                  "joe":{"url":"git://sourceware.org/git/binutils-gdb.git","workflow":"readonly","path":"binutils"},
                  }
            config = {"x":{"repos":["jim"]},
                      "y":{"repos":["joe"], "fred":{"path":"nothing"}},
            }
            pass
        config_name : Union [None, bool, str] = None
        config_name = None
        pass
    class Working(Test):
        pass
    class BadConfigGivesNone(Test):
        config_name = "unknown_config"
        pass
    class SelectDefaultConfig(Test):
        config_name = None
        cfg_assert = {"name":"x"}
        pass
    class t3(Test):
        config_name = "x"
        cfg_assert = {"name":"x",
                      "repos":{"fred":{"git_url":{"protocol":"ssh", "user":"me", "host":"there", "path":"path/to/thing.git"}, "_path":"thing"}}}
        pass
    class SelectConfigY(Test):
        config_name = "y"
        cfg_assert = {"name":"y", "repos":{"fred":{"_path":"nothing"}}}
        pass
    class t5(Test):
        config_name = "y"
        cfg_assert = {"repos":{"fred":{"workflow":{"name":"readonly"}}}}
        pass
    class t6(Test):
        config_name = "x"
        cfg_assert = {"repos":{"jim":{"workflow":{"name":"single"}}}}
        pass
    class t7(Test):
        config_name = "y"
        cfg_assert = {"repos":{"joe":{"workflow":{"name":"readonly"}}}}
        pass
    class t8(Test):
        config_name = "y"
        cfg_assert = {"repos":{"joe":{"git_url":{"protocol":"git","host":"sourceware.org", "path":"git/binutils-gdb.git"}, "_path":"binutils"}}}
        pass

#c TestConfiguredSubrepos
class SubrepoTomlJoe(Toml):
    doc="subrepo joe doc"
    env = {"SRC":"@GRIP_REPO_PATH@"}
    clean_sim = {"exec":"clean_sim joe"}
    build_sim = {"exec":"build_sim joe"}
    run_sim = {"exec":"run_sim joe", "action":"yes"}

class TestConfiguredSubrepos(TestSet):
    class Test(TestBase):
        class ConfigToml(Toml):
            name="y"
            workflow="readonly"
            default_config="x"
            configs=["x","y"]
            base_repos=["fred"]
            repo:Dict[str,Any]={}
            repo={"fred":{"url":'ssh://me@there/path/to/thing.git'},
                  "jim":{"url":'some/path/to/jim.git',"workflow":"single"},
                  "joe":{"url":"git://sourceware.org/git/binutils-gdb.git","workflow":"readonly","path":"binutils"},
                  }
            config = {"x":{"repos":["jim"]},
                      "y":{"repos":["joe"], "fred":{"path":"nothing"}},
            }
            pass
        config_name : Union [None, bool, str] = None
        config_name = None
        subrepos : SubrepoTomls = {"binutils":SubrepoTomlJoe}
        pass
    class Working(Test):
        config_name = "y"
        cfg_assert = {"repos":{"joe":{"_path":"binutils"}}}
        pass
    class SubrepoJoeEnv(Test):
        config_name = "y"
        cfg_assert = {"repos":{"joe":{"doc":"subrepo joe doc"}}}
        pass

#c TestStages
class TestStages(TestSet):
    class Test(TestBase):
        class ConfigToml(Toml):
            name="stages"
            workflow="readonly"
            default_config="x"
            configs=["x","y"]
            base_repos=["fred"]
            repo:Dict[str,Any]={}
            repo= {
                "fred": {
                    "url":'ssh://me@there/path/to/thing.git',
                    "build":{"exec":"build_fred"},
                },
                "jim": {
                    "url":'some/path/to/jim.git',"workflow":"single",
                    "build":{"exec":"build_jim"},
                },
                "joe": {
                    "url":"git://sourceware.org/git/binutils-gdb.git","workflow":"readonly","path":"binutils",
                    "build":{"exec":"build_joe"},
                },
            }
            # Want to support [stage.some] ... but we do not as yet
            # stage = {"some":{"doc":"doc of stage some"}}
            config = {
                "x": {
                    "repos":["jim"],
                    "stage":{"all":{"doc":"doc of stage all in cfg x",
                                    "exec":"some_exec for x",
                                    "requires":["fred.build"]}},
                    "env":{"A":"v"},
                },
                "y": {
                    "repos":["joe"],
                    "stage":{"all":{"doc":"doc of stage all in cfg y",
                                    "exec":"some_exec",
                                    "requires":["joe.build", "fred.build"]}},
                    "fred":{"path":"nothing"},
                },
            }
            pass
        config_name : Union [None, bool, str] = None
        config_name = None
        pass
    class Working(Test):
        config_name = "y"
        cfg_assert : Asserts = {"stages":{"all":{"doc":"doc of stage all in cfg y"}}}
        pass
    class StageFredBuild(Test):
        cfg_assert : Asserts = {"repos":{"fred":{"stages":{"build":{"exec":"build_fred"}}}}}
        pass
    class StageAll1(Test):
        cfg_assert : Asserts = {"stages":{"all":{"doc":"doc of stage all in cfg x"}}}
        pass
    class StageAll1Exec(Test):
        config_name = "y"
        cfg_assert : Asserts = {"stages":{"all":{"exec":"some_exec"}}}
        pass
    pass

#a Toplevel
#f Create tests
TestUnconfigured._create_test_fns_of_class(TestUnconfigured.Test)
TestConfigured._create_test_fns_of_class(TestConfigured.Test)
TestConfiguredSubrepos._create_test_fns_of_class(TestConfiguredSubrepos.Test)
TestStages._create_test_fns_of_class(TestStages.Test)
test_suite = [TestUnconfigured, TestConfigured, TestConfiguredSubrepos, TestStages]
