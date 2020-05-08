#a Imports
import toml
from typing import Dict, Optional, Any
from ..tomldict import RawTomlDict, TomlDict, TomlDictValues, TomlDictParser
from ..exceptions import *
from ..descriptor import ConfigurationDescriptor as ConfigDescriptor

from ..types import PrettyPrinter, Documentation, MakefileStrings

#a Toml parser classes - description of a .grip/grip.toml file
#c *..TomlDict subclasses to parse toml file contents
class GripStateTomlDict(TomlDict):
    """Dictionary of config name -> configuration state
        """
    class ConfigTomlDict(TomlDict):
        """Dictionary of repo name -> configuration state
        """
        class RepoStateTomlDict(TomlDict):
            """
            changeset = <>
            branch - used in some workflows (not readonly or single, but would be in deity or pullrequest)
            possibly a url is required for deity (this may be a remote specifier instead if grip repo descs support more than one remote per repo, e.g. one for pull, one for push)
            depth - should be an integer specifying how deep in to the git repo the changeset was on the branch, for shallow pulls
            """
            changeset    = TomlDictParser.from_dict_attr_value(str)
            branch        = TomlDictParser.from_dict_attr_value(str)
            depth         = TomlDictParser.from_dict_attr_value(int)
            pass
        Wildcard     = TomlDictParser.from_dict_attr_dict(RepoStateTomlDict)
        pass
    Wildcard     = TomlDictParser.from_dict_attr_dict(ConfigTomlDict)
    pass
class RepoStateTomlDictValues(TomlDictValues):
    """
    Only for typing - this mirrors the created TomlDictValues magic instance
    """
    changeset : Optional[str]
    branch    : Optional[str]
    depth     : Optional[int]
    pass

#a Classes
#c GitRepoState - state for a repo in a particular config
class GitRepoState(object):
    """
    A git repository inside a grip repo must point to a particular changeset
    This changeset would normally be on the same branch as the grip repo specifies,
    but for some workflows
    """
    changeset: Optional[str] = None
    branch   : Optional[str] = None
    depth    : Optional[int] = None
    #f __init__
    def __init__(self, name:str, repo_desc_config:Optional[ConfigDescriptor]=None, values:Optional[RepoStateTomlDictValues]=None):
        """
        values must be a RepoStateTomlDict._values
        """
        self.name   = name
        if values is not None:
            self.changeset = values.changeset
            self.branch    = values.branch
            self.depth     = values.depth
            pass
        if repo_desc_config is not None:
            r = repo_desc_config.get_repo(self.name)
            if r is None: raise Exception("Did not find repo %s"%self.name)
            if self.branch is None: self.branch = r.branch
            pass
        pass
    #f update_state
    def update_state(self, changeset:Optional[str]=None) -> None:
        if changeset is not None: self.changeset = changeset
        pass
    #f toml_dict
    def toml_dict(self) -> Dict[str,Any]:
        toml_dict : Dict[str, Any] = {"changeset":self.changeset}
        if self.branch is not None: toml_dict["branch"] = self.branch
        if self.depth  is not None: toml_dict["depth"] = self.depth
        return toml_dict
    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        acc = pp(acc, "repo.%s:%s" % (self.name, self.changeset))
        return acc
    #f All done
    pass

#c GripConfig - a set of GripRepoState's for a configuration of the grip repo
class GripConfig(object):
    """
    A GripConfig describes a configuration of a grip repo.

    A grip repo configuration is a set of git repos, and for each git repo the relevant commands and dependencies
    to install, test_install, make, run, test and precommit

    In a grip.toml file, the GripConfig is described using
    [config.<name>]
    repos = [ list of repo names specific to the config]
    <repo>.<stage> = <toml of a GitRepoStageDesc>
    """
    repos : Dict[str, GitRepoState] = {} # dictionary of <repo name> : <GitRepoState instance>
    #f __init__
    def __init__(self, name:str, values:Optional[TomlDictValues]=None):
        self.name = name
        self.repos = {}
        if values is not None:
            self.build_from_values(values)
            pass
        pass
    #f build_from_values
    def build_from_values(self, values:TomlDictValues) -> None:
        """
        values is a ConfigTomlDict._values

        Hence it has other attributes that should be <reponame> of type RepoStateTomlDict._values
        """
        self.repos = {}
        for r in values.Get_other_attrs(): # These must be RepoDescTomDict._values
            repo_state = values.Get(r)
            self.repos[r] = GitRepoState(r, values=repo_state)
            pass
        pass
    #f toml_dict
    def toml_dict(self) -> Dict[str,Any]:
        toml_dict : Dict[str,Any] = {}
        for (n,r) in self.repos.items():
            toml_dict[n] = r.toml_dict()
            pass
        return toml_dict
    #f get_repo_state
    def get_repo_state(self, repo_desc_config:Optional[ConfigDescriptor], repo_name:str, create_if_new:bool=True) -> Optional[GitRepoState]:
        """
        Get state of a repo from its name
        If there is not a repo of that name, possibly create it
        """
        if repo_name not in self.repos:
            if not create_if_new: return None
            self.repos[repo_name] = GitRepoState(repo_name, repo_desc_config=repo_desc_config)
            pass
        return self.repos[repo_name]
    #f update_repo_state
    def update_repo_state(self, repo_name:str, **kwargs:Any) -> None:
        """
        Update state of a repo from its name
        """
        if repo_name not in self.repos: raise Exception("Bug - updating repo state for %s.%s which does not exist"%(self.name,repo_name))
        return self.repos[repo_name].update_state(**kwargs)
    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        acc = pp(acc, "config.%s:" % (self.name))
        for r in self.repos:
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent+1)
            acc = self.repos[r].prettyprint(acc, ppr)
            pass
        return acc
    #f All done
    pass

#c StateFile - complete description of a grip repo, from the grip toml file
class StateFile(object):
    """
    """
    raw_toml_dict = None
    configs : Dict[str, GripConfig] = {}
    #f __init__
    def __init__(self) -> None:
        self.configs = {}
        pass
    #f read_toml_dict
    def read_toml_dict(self, toml_dict:RawTomlDict) -> None:
        self.raw_toml_dict = toml_dict
        values = TomlDictParser.from_dict(GripStateTomlDict, "", self.raw_toml_dict)
        self.build_from_values(values)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename:str) -> None:
        """
        Load the <root_dir>/.grip/state.toml file
        """
        try:
            toml_dict = toml.load(grip_toml_filename)
            return self.read_toml_dict(toml_dict)
        except FileNotFoundError:
            pass
        pass
    #f read_toml_string
    def read_toml_string(self, grip_toml_string:str) -> None:
        """
        Really used in test only, read description from string
        """
        return self.read_toml_dict(toml.loads(grip_toml_string))
    #f write_toml_file
    def write_toml_file(self, grip_toml_filename:str) -> None:
        """
        Write the <root_dir>/.grip/state.toml file
        """
        toml_dict = self.toml_dict()
        toml_string = toml.dumps(toml_dict)
        with open(grip_toml_filename,"w") as f:
            f.write(toml_string)
            pass
        pass
    #f build_from_values
    def build_from_values(self, values:TomlDictValues) -> None:
        self.configs = {}
        for config_name in values.Get_other_attrs():
            self.configs[config_name] = GripConfig(config_name, values=values.Get(config_name))
            pass
        pass
    #f toml_dict
    def toml_dict(self) -> Dict[str,Any]:
        toml_dict = {}
        for (n,c) in self.configs.items():
            toml_dict[n] = c.toml_dict()
            pass
        return toml_dict
    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        for c in self.configs:
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent)
            acc = self.configs[c].prettyprint(acc, ppr)
            pass
        return acc
    #f select_config
    def select_config(self, config_name:str, create_if_new:bool=True) -> Optional[GripConfig]:
        """
        Return a selected configuration
        """
        if config_name not in self.configs:
            if not create_if_new: return None
            self.configs[config_name] = GripConfig(config_name)
            pass
        return self.configs[config_name]
    #f All done
    pass

