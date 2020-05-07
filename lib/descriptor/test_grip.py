#a Imports
from typing import Optional, Dict, Sequence, Collection, Any, Union, Type
from ..exceptions import *
from ..tomldict import TomlDict, TomlDictParser
from ..git import Repository as GitRepo
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict
from .stage import Dependency as StageDependency
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict
from .repo  import RepoDescTomlDict
from .repo  import Descriptor as GitRepoDesc
from .config import Descriptor as ConfigDescriptor
from .config import ConfigTomlDict

#a Unittest for GripRepoDesc class
from ..test_utils import UnitTestObject
class GripRepoDescUnitTestBase(UnitTestObject):
    config_toml : Optional[str]= None
    config_name : Union [None, bool, str] = False
    grd_assert  : Optional[ Dict[str, Any]] = None
    cfg_assert  : Optional[ Dict[str, Any]] = None
    exception_expected : Optional[Type[Exception]]= None
    def test_it(self):
        def git_repo():pass
        git_repo.get_git_url_string = lambda:""
        git_repo.get_path = lambda:""
        if self.config_toml is not None:
            grd = GripRepoDesc(git_repo=git_repo)
            if self.exception_expected is not None:
                self.assertRaises(self.exception_expected, grd.read_toml_string, self.config_toml)
                pass
            else:
                grd.read_toml_string(self.config_toml)
                pass
            if self.grd_assert is not None:
                self._test_obj_asserts(grd, self.grd_assert, "grip_repo_desc")
                pass
            if self.config_name is not False:
                cfg = grd.select_config(config_name=self.config_name)
                if cfg is None:
                    self.assertEqual(cfg, self.cfg_assert)
                    pass
                else:
                    self._test_obj_asserts(cfg, self.cfg_assert, "config_desc")
                    pass
                pass
            pass
        pass
    pass
class GripRepoDescUnitTest1(GripRepoDescUnitTestBase):
    """
    Note that only configuration's repodescs have resolved git_url properties
    """
    config_toml = """name="y"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=[]\nrepo={}\n"""
    grd_assert = {"name":"y","default_config":"x", "base_repos":[]}
    pass
class GripRepoDescUnitTestBadDefaultConfig(GripRepoDescUnitTestBase):
    exception_expected = RepoDescError
    config_toml = """name="y"\ndefault_config="ax"\nconfigs=["x"]\nbase_repos=[]\nrepo={}\n"""
    pass
class GripRepoDescUnitTest2(GripRepoDescUnitTestBase):
    config_toml = """name="y"\nworkflow="readonly"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=["fred"]\nrepo.fred={url='a',path='b'}\n"""
    grd_assert = {"base_repos":["fred"],
                  "repos":{
                      "fred":{"name":"fred","url":"a","path":"b"},
                  }
    }
    pass
class GripRepoDescUnitTest3(GripRepoDescUnitTestBase):
    config_toml = """name="y"\nworkflow="readonly"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=[]\nrepo.fred={url='a',path='b'}\n"""
    grd_assert = {"base_repos":[],
                  "repos":{
                      "fred":{"name":"fred","url":"a","path":"b"},
                  }
    }
    pass
class GripRepoDescUnitTest4(GripRepoDescUnitTestBase):
    config_toml = """name="y"\nworkflow="readonly"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=[]\nrepo.fred={url='a',path='b'}\n"""
    grd_assert = {"base_repos":[],
                  "repos":{
                      "fred":{"name":"fred","url":"a","path":"b"},
                  }
    }
    pass
class GripRepoDescUnitTestBadBaseRepos(GripRepoDescUnitTestBase):
    exception_expected = RepoDescError
    config_toml = """name="y"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=["f"]\nrepo.fred={url='a',path='b'}\n"""
    pass
class GripRepoDescUnitTestConfigBase(GripRepoDescUnitTestBase):
    config_toml = """
    name="y"
    workflow="readonly"
    default_config="x"
    configs=["x","y"]
    base_repos=["fred"]
    repo.fred={url='ssh://me@there/path/to/thing.git'}
    repo.jim={url='some/path/to/jim.git',workflow="single"}
    repo.joe={url='git://sourceware.org/git/binutils-gdb.git',workflow="readonly",path="binutils"}
    config.x.repos = ["jim"]
    config.y.fred.path = "nothing"
    config.y.repos = ["joe"]
    """
    pass
class GripRepoDescUnitTestConfig1(GripRepoDescUnitTestConfigBase):
    config_name = "unknown_config"
    cfg_assert = None
    pass
class GripRepoDescUnitTestConfig2(GripRepoDescUnitTestConfigBase):
    config_name = None # default
    cfg_assert = {"name":"x"}
    pass
class GripRepoDescUnitTestConfig3(GripRepoDescUnitTestConfigBase):
    config_name = "x"
    cfg_assert = {"name":"x", "repos":{"fred":{"git_url":{"protocol":"ssh", "user":"me", "host":"there", "path":"path/to/thing.git"}, "path":"thing"}}}
    pass
class GripRepoDescUnitTestConfig4(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"name":"y", "repos":{"fred":{"path":"nothing"}}}
    pass
class GripRepoDescUnitTestConfig5(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"fred":{"workflow":{"name":"readonly"}}}}
    pass
class GripRepoDescUnitTestConfig6(GripRepoDescUnitTestConfigBase):
    config_name = "x"
    cfg_assert = {"repos":{"jim":{"workflow":{"name":"single"}}}}
    pass
class GripRepoDescUnitTestConfig7(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"joe":{"workflow":{"name":"readonly"}}}}
    pass
class GripRepoDescUnitTestConfig8(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"joe":{"git_url":{"protocol":"git","host":"sourceware.org", "path":"git/binutils-gdb.git"}, "path":"binutils"}}}
    pass


