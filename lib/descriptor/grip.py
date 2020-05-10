#a Imports
import os, sys, re, copy
import toml
from typing import Type, Optional, Dict, List, Tuple, Any, Iterator, Sequence, Mapping, Union, cast, Iterable
from ..base        import GripBase
from ..exceptions import *
from ..tomldict import RawTomlDict, TomlDict, TomlDictValues, TomlDictParser
from ..git import Repository as GitRepository
from ..git import Url as GitUrl
from ..workflow import Workflow, get_workflow, supported_workflows
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict
from .stage import Dependency as StageDependency
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict
from .repo  import RepoDescTomlDict
from .repo  import Descriptor as RepositoryDescriptor
from .repo  import DescriptorInConfig as RepositoryDescriptorInConfig
from .config import Descriptor as ConfigurationDescriptor
from .config import ConfigTomlDict

from typing import TYPE_CHECKING
from ..types import PrettyPrinter, Documentation, DocumentationEntry, MakefileStrings, EnvDict
if TYPE_CHECKING:
    from ..grip import Toplevel
    from ..workflow import Workflow

#a Useful functions
def str_keys(d:Mapping[str,Any]) -> str:
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
class GripFileTomlDictValues(TomlDictValues):
    base_repos : Optional[List[str]]
    stages :     Optional[List[str]]
    config :     Optional[TomlDictValues]
    repo   :     Optional[TomlDictValues]
    env    :     Optional[TomlDictValues]
    pass
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
    env : TomlDictValues
    def __init__(self, values:GripFileTomlDictValues):
        values.Set_obj_properties(self, ["name", "workflow", "base_repos", "default_config", "logging", "doc", "configs", "stages", "config", "repo", "env"])
        if values.base_repos is None: self.base_repos=[]
        if values.stages     is None: self.stages=[]
        if values.env        is None: self.env=TomlDictValues(EnvTomlDict)
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
    configs        : Dict[str,ConfigurationDescriptor]
    repos          : Dict[str,RepositoryDescriptor]
    stages         : Dict[str,StageDescriptor]
    re_valid_name = re.compile(r"[a-zA-Z0-9_]*$")
    workflow : Type[Workflow]
    selected_config : Optional[ConfigurationDescriptor] = None
    #f __init__
    def __init__(self, base:GripBase):
        self.base     = base
        self.git_repo = base.get_git_repo()
        default_env = {}
        default_env["GRIP_ROOT_URL"]  = self.git_repo.get_git_url_string()
        default_env["GRIP_ROOT_PATH"] = self.git_repo.get_path()
        default_env["GRIP_ROOT_DIR"]  = os.path.basename(self.git_repo.get_path())
        self.env = GripEnv(name='grip.toml', default_values=default_env)
        pass
    #f toml_loads
    def toml_loads(self, filename:str, s:str) -> RawTomlDict:
        """
        A wrapper around toml.loads to provide a suitable error on an exception
        """
        try:
            r = toml.loads(s)
            pass
        except toml.decoder.TomlDecodeError as e: # type:ignore
            raise(ConfigurationError("Toml file '%s' failed to read: %s"%(filename, str(e))))
        return r
    #f read_toml_strings
    def read_toml_strings(self, grip_toml_string:str, subrepo_toml_strings:Dict[str,str], filename:str="<toml_file>")->None:
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
        values = TomlDictParser.from_dict(GripFileTomlDict, "", self.raw_toml_dict)
        pass
    #f build_from_toml_dict
    def build_from_toml_dict(self) -> None:
        """
        Create the description and validate it from the grip_toml_string contents
        """
        values = TomlDictParser.from_dict(GripFileTomlDict, "", self.raw_toml_dict)
        values = cast(GripFileTomlDictValues, values)
        # values.Prettyprint()
        self.build_from_values(values)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename:str, subrepo_descs:List[RepositoryDescriptorInConfig]=[], error_handler:ErrorHandler=None) -> None:
        """
        Load the <root_dir>/.grip/grip.toml file

        subrepo_descs is a list of RepoDescriptor instances which may have been checked
        out which may have grip.toml files. Add these after the main file.
        """
        self.base.add_log_string("Reading config toml file '%s'"%(grip_toml_filename))
        with open(grip_toml_filename) as f:
            toml_string = f.read()
            pass
        subrepo_toml_strings = {}
        for r in subrepo_descs:
            srfn = self.git_repo.filename([r.get_path(),"grip.toml"])
            self.base.add_log_string("Trying to read subconfig toml file '%s'"%(srfn))
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
    def build_from_values(self, values:GripFileTomlDictValues) -> None:
        self.values = DescriptorValues(values)
        # Would like to support no repos
        # if len(self.values.repo)==0:    raise GripTomlError("'repo' entries must be provided (empty grip configuration is not supported)")
        if len(self.values.configs)==0: raise GripTomlError("'configs' must be provided in grip configuration file")
        if self.values.default_config is None:
            raise GripTomlError("default_config must bre provided in grip configuration file")
        self.default_config = self.values.default_config
        if self.default_config not in self.values.configs:
            raise GripTomlError("default_config '%s' must be in 'configs' (which are %s)"%(self.values.default_config,self.values.configs))
        self.name           = self.values.name
        self.base_repos     = self.values.base_repos
        self.logging        = self.values.logging
        self.doc            = self.values.doc
        self.env.build_from_values(self.values.env)
        # Must validate the base_repos here so users can assume self.repos[x] is valid for x in self.base_repos
        for r in self.values.base_repos:
            if r not in self.values.repo: raise RepoDescError("repo '%s', one of the base_repos, is not one of the repos described (which are %s)"%(r, str_keys(self.values.repo)))
            pass
        # Build stages before configs
        self.repos = {}
        for (repo_name, repo_values) in self.values.repo.items():
            self.repos[repo_name] = RepositoryDescriptor(repo_name, values=repo_values, grip_repo_desc=self)
            pass
        self.stages = {}
        for s in self.values.stages:
            self.stages[s] = StageDescriptor(grip_repo_desc=self, name=s, values=None)
            pass
        self.configs = {}
        for config_name in self.values.configs:
            self.base.add_log_string("Noting values for config '%s'"%config_name)
            self.configs[config_name] = ConfigurationDescriptor(config_name, self)
            pass
        for (config_name, config_desc) in self.configs.items():
            self.base.add_log_string("Build values for config '%s'"%config_name)
            config_values = None
            if config_name in self.values.config:
                config_values = self.values.config[config_name]
            config_desc.build_from_values(config_values)
            pass
        pass
    #f validate
    def validate(self, error_handler:ErrorHandler=None) -> None:
        if self.name is None:
            raise RepoDescError("Unnamed repo descriptors are not permitted - the .grip/grip.toml file should have a toplevel 'name' field")
        if self.re_valid_name.match(self.name) is None:
            raise RepoDescError("Names of grip repos must consist only of A-Z, a-z, 0-9 and _ characters (got '%s')"%(self.name))
        self.env.resolve(error_handler=error_handler)
        if self.default_config not in self.configs:
            raise RepoDescError("default_config of '%s' is undefined (defined configs are %s)" % (self.default_config, str_keys(self.configs)))
        if self.values.workflow is None:
            raise RepoDescError("workflow must be defined")
        self.workflow = self.validate_workflow(self.values.workflow, "grip repo description")
        for c in self.iter_configs():
            c.validate(error_handler=error_handler)
            pass
        if self.logging is None: self.logging=False
        pass
    #f iter_configs:
    def iter_configs(self) -> Iterable[ConfigurationDescriptor]:
        if self.selected_config is None:
            for (n,c) in self.configs.items():
                yield(c)
                pass
        else:
            yield(self.selected_config)
            pass
        pass
    #f resolve
    def resolve(self, error_handler:ErrorHandler=None) -> None:
        """
        Resolve any values using grip environment variables to config or default values
        """
        for c in self.iter_configs():
            c.resolve(error_handler=error_handler)
            pass
        pass
    #f validate_workflow - map from workflow name to workflow class
    def validate_workflow(self, workflow:str, user:str) -> Type[Workflow]:
        if workflow is None:
            raise RepoDescError("'%s' is does not have a workflow specified"%(user))
        w = get_workflow(workflow)
        if w is None:
            raise RepoDescError("workflow '%s' used in %s is not in workflows supported by this version of grip (which are %s)"%(workflow, user, supported_workflows()))
        return w
    #f iter_repos - iterate over repos in config, each is RepoDescriptor instance
    def iter_repos(self) -> Iterator[RepositoryDescriptor]:
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
    #f get_name - get name or ""
    def get_name(self) -> str:
        if self.name is None: return ""
        return self.name
    #f get_configs - get names of configs
    def get_configs(self) -> List[str]:
        return list(self.configs.keys())
    #f get_stage - used by Config
    def get_stage(self, stage_name:str) -> Optional[StageDescriptor]:
        """
        Get dictionary of stage name -> Stage
        """
        if stage_name in self.stages: return self.stages[stage_name]
        return None
    #f get_repo - used by Config
    def get_repo(self, repo_name:str) -> Optional[RepositoryDescriptor]:
        """
        Get dictionary of stage name -> Stage
        """
        if repo_name in self.repos: return self.repos[repo_name]
        return None
    #f get_doc_string
    def get_doc_string(self) -> str:
        """
        Return documentation string
        """
        if self.doc is None: return "Undocumented"
        return self.doc.strip()
    #f get_doc
    def get_doc(self, include_configs:bool=True) -> Documentation:
        """
        Return documentation = list of <string> | (name * documentation)
        List should include all configurations
        List should always start with (None, repo.doc) if there is repo doc
        """
        r : Documentation = []
        r.append(self.get_doc_string())
        if include_configs:
            for (n,c) in self.configs.items():
                r.append(("********************************************************************************"))
                r.append(("reinsntate configration get doc string in description/grip.py"))
                #r.append(("Configuration %s"%n,c.get_doc_string()))
                pass
            pass
        return r
    #f is_logging_enabled
    def is_logging_enabled(self) -> bool:
        return self.logging
    #f select_config
    def select_config(self, config_name:Optional[str]=None) -> Optional[ConfigurationDescriptor]:
        """
        Return a selected configuration
        """
        self.selected_config = None
        if config_name is None: config_name=self.default_config
        if config_name not in self.configs: return None
        self.selected_config = self.configs[config_name]
        return self.configs[config_name]
    #f resolve_git_urls
    def resolve_git_urls(self, grip_git_url:GitUrl) -> None:
        """
        Resolve all relative (and those using environment variables?) git urls
        """
        for c in self.iter_configs():
            c.resolve_git_urls(grip_git_url)
            pass
        pass
    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        acc = pp(acc, "default_config: %s"%(self.default_config))
        acc = pp(acc, "base_repos:     %s"%(str(self.base_repos)))
        for (n,r) in self.repos.items():
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent)
            acc = r.prettyprint(acc, ppr)
            pass
        for (n,c) in self.configs.items():
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent)
            acc = c.prettyprint(acc, ppr)
            pass
        return acc
    #f All done
    pass

