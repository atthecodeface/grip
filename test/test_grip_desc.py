#a Imports
from typing import Optional, Dict, Sequence, Collection, Any, Union, Type
from lib.exceptions import *
from lib.tomldict import TomlDict, TomlDictParser
from lib.git import Repository as GitRepo
from lib.exceptions import *
from lib.env import GripEnv, EnvTomlDict
from lib.descriptor.stage import Dependency as StageDependency
from lib.descriptor.stage import Descriptor as StageDescriptor
from lib.descriptor.stage import StageTomlDict
from lib.descriptor.repo  import RepoDescTomlDict
from lib.descriptor.grip import Descriptor as GripRepoDesc

from .test_lib.unittest import UnitTestObject, AKV
from .test_lib.unittest import TestCase
from .test_lib.toml_file import Toml

from typing import Dict, List, Any, Optional, Union, cast

#a Unittest for GripRepoDesc class
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
class TestBase(UnitTestObject):
    config_toml_cls = DefaultConfigToml
    config_toml : str
    config_name : Union [None, bool, str] = False
    grd_assert  : Dict[str, Any] = {}
    cfg_assert  : Dict[str, Any] = {}
    exception_expected : Optional[Type[Exception]]= None
    def __init__(self, method_name:str) -> None:
        if hasattr(self, "config_toml_cls"):
            self.config_toml = self.config_toml_cls()._as_string()
            pass
        UnitTestObject.__init__(self, method_name)
        pass
    #f debug_repo_desc
    def debug_repo_desc(self, grd) -> None:
        def p(acc:Any, s:str, indent:int=0) -> Any:
            print(("  "*indent)+s)
        grd.prettyprint("",p)
        pass
    def do_read_toml(self):
        self.grd.read_toml_strings(self.config_toml, {})
        self.grd.validate()
        self.grd.resolve()
        # self.debug_repo_desc(self.grd)
        self.grd.resolve_git_urls(self.git_repo.get_git_url())
        pass
    def test_it(self) -> None:
        if self.config_toml !="":
            # print(self.config_toml)
            self.git_repo = GitRepo(path_str=".", permit_no_remote=True)
            self.grd = GripRepoDesc(git_repo=self.git_repo)
            if self.exception_expected is not None:
                self.assertRaises(self.exception_expected, self.do_read_toml)
                return
            else:
                self.do_read_toml()
                pass
            if len(self.grd_assert)>0:
                self._test_obj_asserts(self.grd, self.grd_assert, "grip_repo_desc")
                pass
            if self.config_name is not False:
                config_name = cast(Optional[str],self.config_name)
                cfg = self.grd.select_config(config_name=config_name)
                if cfg is None:
                    self.assertTrue(len(self.cfg_assert)==0)
                    pass
                else:
                    self._test_obj_asserts(cfg, self.cfg_assert, "config_desc")
                    pass
                pass
            pass
        pass
    pass

#c Test1
class Test1(TestBase):
    """
    Note that only configuration's repodescs have resolved git_url properties
    """
    grd_assert = {"name":"y","default_config":"x", "base_repos":[]}
    pass

#c Test1BadDefaultConfig
class Test1BadDefaultConfig(Test1):
    class config_toml_cls(Test1.config_toml_cls):
        default_config = "<not a defined config>"
        pass
    exception_expected = GripTomlError
    pass

#c Test1WorkflowSingle
class Test1WorkflowSingle(Test1):
    class config_toml_cls(Test1.config_toml_cls):
        workflow="single"
        pass
    pass

#c Test1WorkflowReadonly
class Test1WorkflowReadonly(Test1):
    class config_toml_cls(Test1.config_toml_cls):
        workflow="readonly"
        pass
    pass

#c Test1BadWorkflow
class Test1BadWorkflow(Test1):
    class config_toml_cls(Test1.config_toml_cls):
        workflow="unknown_workflow"
        pass
    exception_expected = RepoDescError
    pass

#c TestRepoUrl
class TestRepoUrl(TestBase):
    class config_toml_cls(TestBase.config_toml_cls):
        base_repos=["fred"]
        repo={"fred":{"url":'a',"path":'b'}}
        pass
    grd_assert = {"base_repos":["fred"],
                  "repos":{
                      "fred":{"name":"fred"}, # Repo is not resolved until configured so url and path are not valid
                  }
    }
    pass

#c TestEmptyBaseRepos
class TestEmptyBaseRepos(TestBase):
    class config_toml_cls(TestBase.config_toml_cls):
        base_repos=[]
        repo={"fred":{"url":'a',"path":'b'}}
        pass
    grd_assert = {"base_repos":[],
                  "repos":{
                      "fred":{},
                  }
    }
    pass

#c TestBadBaseRepos
class TestBadBaseRepos(TestBase):
    class config_toml_cls(TestBase.config_toml_cls):
        base_repos=["tom"]
        repo={"fred":{"url":'a',"path":'b'}}
        pass
    exception_expected = RepoDescError
    pass

#c TestConfigBase
class TestConfigBase(TestBase):
    class config_toml_cls(Toml):
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

#c TestConfigBadConfigGivesNone
class TestConfigBadConfigGivesNone(TestConfigBase):
    config_name = "unknown_config"
    pass

#c TestConfigSelectDefaultConfig
class TestConfigSelectDefaultConfig(TestConfigBase):
    config_name = None
    cfg_assert = {"name":"x"}
    pass

#c TestConfigSelectConfigX
class TestConfig3(TestConfigBase):
    config_name = "x"
    cfg_assert = {"name":"x",
                  "repos":{"fred":{"git_url":{"protocol":"ssh", "user":"me", "host":"there", "path":"path/to/thing.git"}, "path":"thing"}}}
    pass

#c TestConfigSelectConfigY
class TestConfigSelectConfigY(TestConfigBase):
    config_name = "y"
    cfg_assert = {"name":"y", "repos":{"fred":{"path":"nothing"}}}
    pass

#c TestConfig5
class TestConfig5(TestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"fred":{"workflow":{"name":"readonly"}}}}
    pass

#c TestConfig6
class TestConfig6(TestConfigBase):
    config_name = "x"
    cfg_assert = {"repos":{"jim":{"workflow":{"name":"single"}}}}
    pass

#c TestConfig7
class TestConfig7(TestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"joe":{"workflow":{"name":"readonly"}}}}
    pass

#c TestConfig8
class TestConfig8(TestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"joe":{"git_url":{"protocol":"git","host":"sourceware.org", "path":"git/binutils-gdb.git"}, "path":"binutils"}}}
    pass


