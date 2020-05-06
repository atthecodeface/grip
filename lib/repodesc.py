#a Imports
import os, sys, re, copy
import toml
from .tomldict import TomlDict, TomlDictParser
from .git import GitRepo
from .workflows import workflows
from .exceptions import *
from .env import GripEnv, EnvTomlDict
from .stage import Dependency as StageDependency
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict
from .git_repo_desc import RepoDescTomlDict, GitRepoDesc
from .config import GripConfig, ConfigTomlDict

#a Useful functions
def str_keys(d):
    return ", ".join([k for k in d.keys()])

#a Toml parser classes - description of a .grip/grip.toml file
#c *..TomlDict subclasses to parse toml file contents
class GripFileTomlDict(TomlDict):
    class RepoTomlDict(TomlDict):
        Wildcard     = TomlDictParser.from_dict_attr_dict(RepoDescTomlDict)
        pass
    configs        = TomlDictParser.from_dict_attr_list(str)
    stages         = TomlDictParser.from_dict_attr_list(str)
    base_repos     = TomlDictParser.from_dict_attr_list(str)
    default_config = TomlDictParser.from_dict_attr_value(str)
    logging        = TomlDictParser.from_dict_attr_bool()
    repo           = TomlDictParser.from_dict_attr_dict(RepoTomlDict)
    config         = TomlDictParser.from_dict_attr_dict(ConfigTomlDict)
    workflow       = TomlDictParser.from_dict_attr_value(str)
    name           = TomlDictParser.from_dict_attr_value(str)
    env            = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
    doc            = TomlDictParser.from_dict_attr_value(str)
    pass

#a Classes
#c GripRepoDesc - complete description of a grip repo, from the grip toml file
class GripRepoDesc(object):
    """
    A GripRepoDesc is a complete description of the Grip repo

    It is initialized from a <grip repo>/.grip/grip.toml file, and a chosen config

    The RepoDesc is the mechanism that the main code accesses a grip repo

    A GripRepoDesc object is a parsed in-memory version of a <grip repo>/.grip/grip.toml file.

    Attributes:
    -----------
    default_config : <default config string>
    configs    : list of GripConfig object instances
    base_repos : list <repo name> of the repos used in all configurations
    repos      : dict { <repo name> : <git repo description object> }
    stages     : list <stage names>
    workflow   : workflow to use for all repositories unless they override it
    name       : name of repo - used in branchnames
    doc        : documentation
    """
    raw_toml_dict = None
    default_config = None
    base_repos = []
    configs = {}
    repos = {}
    stages = []
    supported_workflows = workflows()
    re_valid_name = re.compile(r"[a-zA-Z0-9_]*$")
    #v static properties
    logging_options = {"True":True, "False":False, "Yes":True, "No":False}
    #f __init__
    def __init__(self, git_repo):
        self.name = None
        self.workflow = None
        self.default_config = None
        self.repos = {}
        self.configs = {}
        self.stages = {}
        self.base_repos = []
        self.doc = None
        self.git_repo = git_repo
        self.logging = None
        default_env = {}
        default_env["GRIP_ROOT_URL"]  = git_repo.get_git_url_string()
        default_env["GRIP_ROOT_PATH"] = git_repo.get_path()
        default_env["GRIP_ROOT_DIR"]  = os.path.basename(git_repo.get_path())
        self.env = GripEnv(name='grip.toml', default_values=default_env)
        pass
    #f toml_loads
    def toml_loads(self, filename, s):
        """
        A wrapper around toml.loads to provide a suitable error on an exception
        """
        try:
            r = toml.loads(s)
            pass
        except toml.decoder.TomlDecodeError as e:
            raise(ConfigurationError("Toml file '%s' failed to read: %s"%(filename, str(e))))
        return r
    #f read_toml_string
    def read_toml_string(self, grip_toml_string, subrepo_toml_strings, filename="<toml_file>", error_handler=None):
        """
        Create the description and validate it from the grip_toml_string contents

        subrepo_toml_strings is a dictionary of repo -> repo_desc

        """
        self.raw_toml_dict = self.toml_loads(filename, grip_toml_string)
        if "repo" in self.raw_toml_dict:
            for (rn,rs) in subrepo_toml_strings.items():
                if rn not in self.raw_toml_dict["repo"]:
                    raise Exception("grip.toml file does not include repo '%s' when that is a subrepo in the current configuration; grip is being abused"%rn)
                cur_dict = self.raw_toml_dict["repo"][rn]
                rtd = self.toml_loads(rn, rs)
                for (k,v) in rtd.items():
                    if k in cur_dict:
                        if type(cur_dict[k])!=type(v):
                            raise(ConfigurationError("grip cannot merge TOML dictionary for repo '%s' key '%s' value '%s' as the types don't match"%(rn,k,v)))
                        if type(v)==str:
                            cur_dict[k]+=v
                        elif type(v)==list:
                            cur_dict[k].extend(v)
                        elif type(v)==dict:
                            for (dk,dv) in v.items():
                                cur_dict[k][dk]=dv
                                pass
                            pass
                        else:
                            raise(ConfigurationError("grip cannot merge TOML dictionary for repo '%s' key '%s' value '%s' as the types don't merge"%(rn,k,v)))
                        pass
                    else:
                        cur_dict[k] = v
                        pass
                    pass
                pass
            pass
        values = TomlDictParser.from_dict(GripFileTomlDict, self, "", self.raw_toml_dict)
        # values.Prettyprint()
        self.build_from_values(values)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename, subrepos=[], error_handler=None):
        """
        Load the <root_dir>/.grip/grip.toml file

        subrepos is a list of GitRepoDesc instances which may have been checked
        out which may have grip.toml files. Add these after the main file.
        """
        with open(grip_toml_filename) as f:
            toml_string = f.read()
            pass
        subrepo_toml_strings = {}
        for r in subrepos:
            srfn = self.git_repo.filename([r.get_path(),"grip.toml"])
            if os.path.isfile(srfn):
                with open(srfn) as f:
                    subrepo_toml_strings[r.name] = f.read()
                    pass
                pass
            pass
        self.read_toml_string(toml_string, subrepo_toml_strings, filename=grip_toml_filename, error_handler=error_handler)
        pass
    #f validate
    def validate(self, error_handler=None):
        if self.name is None:
            raise RepoDescError("Unnamed repo descriptors are not permitted - the .grip/grip.toml file should have a toplevel 'name' field")
        if self.re_valid_name.match(self.name) is None:
            raise RepoDescError("Names of grip repos must consist only of A-Z, a-z, 0-9 and _ characters (got '%s')"%(self.name))
        self.env.resolve(error_handler=error_handler)
        if self.default_config not in self.configs:
            raise RepoDescError("default_config of '%s' is undefined (defined configs are %s)" % (self.default_config, str_keys(self.configs)))
        if self.workflow is not None:
            self.workflow = self.validate_workflow(self.workflow, "grip repo description")
            pass
        for (n,c) in self.configs.items():
            c.validate(error_handler=error_handler)
            pass
        if self.logging is None: self.logging=False
        pass
    #f resolve
    def resolve(self, error_handler=None):
        """
        Resolve any values using grip environment variables to config or default values
        """
        for (n,c) in self.configs.items():
            c.resolve(error_handler=error_handler)
            pass
        pass
    #f validate_workflow
    def validate_workflow(self, workflow, user):
        if workflow is None:
            raise RepoDescError("'%s' is does not have a workflow specified"%(user))
        if workflow not in self.supported_workflows:
            raise RepoDescError("workflow '%s' used in %s is not in workflows supported by this version of grip (which are %s)"%(self.workflow, user, str_keys(self.supported_workflows)))
        return self.supported_workflows[workflow]
    #f build_from_values
    def build_from_values(self, values):
        values.Set_obj_properties(self, {"name", "workflow", "base_repos", "default_config", "logging", "doc"})
        if values.repo           is None: raise GripTomlError("'repo' entries must be provided (empty grip configuration is not supported)")
        if values.configs        is None: raise GripTomlError("'configs' must be provided in grip configuration file")
        self.env.build_from_values(values.env)
        for repo_name in values.repo.Get_other_attrs():
            self.repos[repo_name] = GitRepoDesc(repo_name, values=values.repo.Get(repo_name), grip_repo_desc=self)
            pass
        # Must validate the base_repos here so users can assume self.repos[x] is valid for x in self.base_repos
        for r in self.base_repos:
            if r not in self.repos: raise RepoDescError("repo '%s', one of the base_repos, is not one of the repos described (which are %s)"%(r, str_keys(self.repos)))
            pass
        # Build stages before configs
        self.stages = {}
        if values.stages is not None:
            for s in values.stages:
                self.stages[s] = StageDescriptor(grip_repo_desc=self, name=s, values=None)
                pass
            pass
        for config_name in values.configs:
            self.configs[config_name] = GripConfig(config_name, self)
            pass
        if values.config is not None:
            for config_name in values.config.Get_other_attrs():
                if config_name not in self.configs:
                    raise GripTomlError("'config.%s' provided without '%s' in configs"%(config_name,config_name))
                config = self.configs[config_name]
                config_values= values.config.Get(config_name)
                config.build_from_values(config_values)
                pass
            pass
        pass
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "default_config: %s"%(self.default_config))
        acc = pp(acc, "base_repos:     %s"%(str(self.base_repos)))
        for (n,r) in self.repos.items():
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent)
            acc = r.prettyprint(acc, ppr)
            pass
        for (n,c) in self.configs.items():
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent)
            acc = c.prettyprint(acc, ppr)
            pass
        return acc
    #f iter_repos - iterate over repos in config, each is GitRepoDesc instance
    def iter_repos(self):
        for n in self.repos:
            yield self.repos[n]
            pass
        pass
    #f iter_stages - iterate over stages in config, each is Stage instance
    def iter_stages(self):
        for n in self.stages:
            yield self.stages[n]
            pass
        pass
    #f get_configs
    def get_configs(self):
        return self.configs.keys()
    #f get_stage - used by Config
    def get_stage(self, stage_name):
        """
        Get dictionary of stage name -> Stage
        """
        if stage_name in self.stages: return self.stages[stage_name]
        return None
    #f get_doc_string
    def get_doc_string(self):
        """
        Return documentation string
        """
        if self.doc is None: return "Undocumented"
        return self.doc.strip()
    #f get_doc
    def get_doc(self, include_configs=True):
        """
        Return documentation = list of <string> | (name * documentation)
        List should include all configurations
        List should always start with (None, repo.doc) if there is repo doc
        """
        r = []
        r.append(self.get_doc_string())
        if include_configs:
            for (n,c) in self.configs.items():
                #r.append(("Configuration %s"%n,c.get_doc_string()))
                pass
            pass
        return r
    #f is_logging_enabled
    def is_logging_enabled(self):
        return self.logging
    #f select_config
    def select_config(self, config_name=None):
        """
        Return a selected configuration
        """
        if config_name is None: config_name=self.default_config
        if config_name not in self.configs: return None
        return self.configs[config_name]
    #f resolve_git_urls
    def resolve_git_urls(self, grip_git_url):
        """
        Resolve all relative (and those using environment variables?) git urls
        """
        for (n,c) in self.configs.items():
            c.resolve_git_urls(grip_git_url)
            pass
        pass
    #f All done
    pass

#a Unittest for GripRepoDesc class
from .test_utils import UnitTestObject
class GripRepoDescUnitTestBase(UnitTestObject):
    config_toml = None
    config_name = False
    grd_assert = None
    cfg_assert = None
    exception_expected = None
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


