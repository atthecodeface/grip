#a Imports
import os, sys, re, copy
import toml
from typing import Optional, Dict, List, Tuple, Any, Iterator, Sequence, Union
from ..exceptions import *
from ..tomldict import TomlDict, TomlDictParser, TomlDictValues
from ..git import GitRepo
from ..workflows import workflows
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict
from .stage import Dependency as StageDependency
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict
from .repo  import RepoDescTomlDict
from .repo  import Descriptor as RepoDescriptor
from .config import Descriptor as ConfigDescriptor
from .config import ConfigTomlDict

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
#c DescriptorValues - namespace that contains values from the TomlDict
class DescriptorValues(object):
    name : Optional[str] = None
    default_config : str      = ""
    base_repos : List[str]    = []
    configs : List[str]       = []
    stages  : List[str]       = []
    config  : Dict[str, TomlDictValues]  = {}
    repo    : Dict[str, TomlDictValues]  = {}
    logging : bool = False
    workflow : Optional[str] = None
    doc : Optional[str] = None
    def __init__(self, values):
        values.Set_obj_properties(self, ["name", "workflow", "base_repos", "default_config", "logging", "doc", "configs", "stages", "config", "repo"])
        if values.base_repos is None: self.base_repos=[]
        if values.stages     is None: self.stages=[]
        self.repo={}
        if values.repo is not None:
            for repo_name in values.repo.Get_other_attrs():
                self.repo[repo_name] = values.repo.Get(repo_name)
                pass
            pass
        self.config={}
        if values.config is not None:
            for config_name in values.config.Get_other_attrs():
                self.config[config_name] = values.config.Get(config_name)
                pass
            pass
        pass

#c Descriptor - complete description of a grip repo, from the grip toml file
class Descriptor(object):
    """
    A GripRepoDesc is a complete description of the Grip repo

    It is initialized from a <grip repo>/.grip/grip.toml file, and a chosen config

    The RepoDesc is the mechanism that the main code accesses a grip repo

    A GripRepoDesc object is a parsed in-memory version of a <grip repo>/.grip/grip.toml file.

    Attributes:
    -----------
    default_config : <default config string>
    configs    : list of ConfigDescriptor object instances
    base_repos : list <repo name> of the repos used in all configurations
    repos      : dict { <repo name> : <git repo description object> }
    stages     : list <stage names>
    workflow   : workflow to use for all repositories unless they override it
    name       : name of repo - used in branchnames
    doc        : documentation
    """
    values : DescriptorValues
    name           : Optional[str]
    default_config : Optional[str]
    base_repos     : List[str]
    configs        : Dict[str,ConfigDescriptor]
    repos          : Dict[str,RepoDescriptor]
    stages         : Dict[str,StageDescriptor]
    supported_workflows = workflows()
    re_valid_name = re.compile(r"[a-zA-Z0-9_]*$")
    #f __init__
    def __init__(self, git_repo):
        self.git_repo = git_repo
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
    #f read_toml_strings
    def read_toml_strings(self, grip_toml_string, subrepo_toml_strings, filename="<toml_file>"):
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
    #f build_from_toml_dict
    def build_from_toml_dict(self):
        """
        Create the description and validate it from the grip_toml_string contents
        """
        values = TomlDictParser.from_dict(GripFileTomlDict, self, "", self.raw_toml_dict)
        # values.Prettyprint()
        self.build_from_values(values)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename, subrepos=[], error_handler=None):
        """
        Load the <root_dir>/.grip/grip.toml file

        subrepos is a list of RepoDescriptor instances which may have been checked
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
        self.read_toml_strings(toml_string, subrepo_toml_strings, filename=grip_toml_filename)
        self.build_from_toml_dict()
        pass
    #f build_from_values
    def build_from_values(self, values):
        self.values = DescriptorValues(values)
        if len(self.values.repo)==0:    raise GripTomlError("'repo' entries must be provided (empty grip configuration is not supported)")
        if len(self.values.configs)==0: raise GripTomlError("'configs' must be provided in grip configuration file")
        self.name           = self.values.name
        self.default_config = self.values.default_config
        self.base_repos     = self.values.base_repos
        self.workflow       = self.values.workflow
        self.logging        = self.values.logging
        self.doc            = self.values.doc
        self.env.build_from_values(values.env)
        # Must validate the base_repos here so users can assume self.repos[x] is valid for x in self.base_repos
        for r in self.values.base_repos:
            if r not in self.values.repo: raise RepoDescError("repo '%s', one of the base_repos, is not one of the repos described (which are %s)"%(r, str_keys(self.values.repo)))
            pass
        # Build stages before configs
        self.repos = {}
        for (repo_name, repo_values) in self.values.repo.items():
            self.repos[repo_name] = RepoDescriptor(repo_name, values=repo_values, grip_repo_desc=self)
            pass
        self.stages = {}
        for s in self.values.stages:
            self.stages[s] = StageDescriptor(grip_repo_desc=self, name=s, values=None)
            pass
        self.configs = {}
        for config_name in self.values.configs:
            self.configs[config_name] = ConfigDescriptor(config_name, self)
            pass
        for (config_name, config_values) in self.values.config.items():
            if config_name not in self.configs:
                raise GripTomlError("'config.%s' provided without '%s' in configs"%(config_name,config_name))
            self.configs[config_name].build_from_values(config_values)
            pass
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
    #f validate_workflow - map from workflow name to workflow class
    def validate_workflow(self, workflow, user):
        if workflow is None:
            raise RepoDescError("'%s' is does not have a workflow specified"%(user))
        if workflow not in self.supported_workflows:
            raise RepoDescError("workflow '%s' used in %s is not in workflows supported by this version of grip (which are %s)"%(self.workflow, user, str_keys(self.supported_workflows)))
        return self.supported_workflows[workflow]
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
    #f iter_repos - iterate over repos in config, each is RepoDescriptor instance
    def iter_repos(self) -> Iterator[RepoDescriptor]:
        for n in self.repos:
            yield self.repos[n]
            pass
        pass
    #f iter_stages - iterate over stages in config, each is Stage instance
    def iter_stages(self) -> Iterator[StageDescriptor]:
        for n in self.stages:
            yield self.stages[n]
            pass
        pass
    #f get_configs - get names of configs
    def get_configs(self) -> List[str]:
        return list(self.configs.keys())
    #f get_stage - used by Config
    def get_stage(self, stage_name) -> Optional[StageDescriptor]:
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
    def get_doc(self, include_configs=True) -> Sequence[ Union [ str, List[ Tuple[str, Any]]]]:
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
    def is_logging_enabled(self) -> bool:
        return self.logging
    #f select_config
    def select_config(self, config_name=None) -> Optional[ConfigDescriptor]:
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

