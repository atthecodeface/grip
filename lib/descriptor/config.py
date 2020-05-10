#a Imports
import os, sys, re, copy
from typing import Dict, Type, Mapping, Any, List, Optional, Iterable, Callable, IO, cast
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict
from ..tomldict import TomlDict, TomlDictValues, TomlDictParser
from ..git import Url as GitUrl
from .stage import StageTomlDict
from .repo  import RepoDescTomlDict
from .stage import Descriptor as StageDescriptor
from .repo import DescriptorInConfig as RepositoryDescriptorInConfig

from typing import TYPE_CHECKING
from ..types import PrettyPrinter, Documentation, DocumentationEntry, MakefileStrings, EnvDict
if TYPE_CHECKING:
    from ..descriptor import GripDescriptor
    from ..grip import Toplevel
    from ..workflow import Workflow

#a Useful functions
def str_keys(d:Mapping[str,Any]) -> str:
    return ", ".join([k for k in d.keys()])

class StageConfigTomlDict(TomlDict):
    Wildcard     = TomlDictParser.from_dict_attr_dict(StageTomlDict)
    pass
class ConfigTomlDict(TomlDict):
        """
        Config is a dictionary of <config name> -> <config description>

        A <config description> has:

        repos = [list of repo names to use in addition to base_repos]
        env   = environment (overriding the global environment)
        doc   = documentation
        stage = dictionary of (<stage_name> -> <stage description>)
        <repo_name> -> repo description
        """
        class SpecificConfigTomlDict(TomlDict):
            """Configuration description: repos, and repo descriptions
            """
            repos        = TomlDictParser.from_dict_attr_list(str)
            env          = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
            doc          = TomlDictParser.from_dict_attr_value(str)
            stage        = TomlDictParser.from_dict_attr_dict(StageConfigTomlDict)
            Wildcard     = TomlDictParser.from_dict_attr_dict(RepoDescTomlDict)
            pass
        Wildcard     = TomlDictParser.from_dict_attr_dict(SpecificConfigTomlDict)
        pass

#c DescriptorValues - namespace that contains values from the TomlDict
class DescriptorValues(object):
    repos: List[str] = []
    env:   TomlDictValues = None # type: ignore
    doc:   Optional[str]
    stage: TomlDictValues
    #f __init__
    def __init__(self, values:Optional[TomlDictValues]):
        if values is None:
            self.env   = TomlDictValues(EnvTomlDict)
            self.stage = TomlDictValues(StageConfigTomlDict)
            return
        values.Set_obj_properties(self, values.Get_fixed_attrs())
        if values.IsNone("env"):   self.env   = TomlDictValues(EnvTomlDict)
        if values.IsNone("stage"): self.stage = TomlDictValues(StageConfigTomlDict)
        pass
    pass

#c Descriptor - a set of GripRepoDesc's for a configuration of the grip repo
class Descriptor(object):
    """
    This describes a configuration of a grip repo.

    A grip repo configuration is a set of git repos, and for each git repo the relevant commands and dependencies
    to install, test_install, make, run, test and precommit

    """
    values : DescriptorValues
    repos  : Dict[str,RepositoryDescriptorInConfig] = {}
    stages : Dict[str,StageDescriptor] = {}
    name   : str
    doc    : Optional[str]
    grip_repo_desc : 'GripDescriptor'
    #f __init__
    def __init__(self, name:str, grip_repo_desc:'GripDescriptor'):
        self.name = name
        self.doc = None
        self.grip_repo_desc = grip_repo_desc
        self.env = GripEnv(name="config '%s'"%self.name,
                           parent=grip_repo_desc.env )
        pass
    #f build_from_values
    def build_from_values(self, values:Optional[TomlDictValues]) -> None:
        """
        values is a SpecificConfigTomlDict._values

        Hence it has a .doc, .repos (possibly None) and other attributes that should be <reponame> of type RepoDescTomlDict._values
        """
        self.values = DescriptorValues(values)
        self.env.build_from_values(self.values.env)
        # Build repos before stages, as stages refer to the repos
        self.build_repos_from_values(values)
        self.build_stages_from_values()
        self.grip_repo_desc.base.add_log_string("Built config '%s' from values containing stages '%s' and repos '%s'"%(self.name, str_keys(self.stages), str_keys(self.repos)))
        pass
    #f build_repos_from_values
    def build_repos_from_values(self, values:Optional[TomlDictValues]) -> None:
        """
        """
        self.repos = {}
        repo_names = set()
        for rn in self.grip_repo_desc.base_repos:
            repo_names.add(rn)
            pass
        for rn in self.values.repos:
            repo_names.add(rn)
            pass
        unconfigured_repos = {}
        for rn in repo_names:
            opt_unconfigured_repo = self.grip_repo_desc.get_repo(rn)
            if opt_unconfigured_repo is None:
                raise GripTomlError("repo '%s' specified in config '%s' but it is not defined in the file"%(rn, self.name))
            unconfigured_repos[rn] = opt_unconfigured_repo
            pass
        repo_descs_just_for_config = {}
        if values is not None:
            for rn in values.Get_other_attrs(): # These must be RepoDescTomDict._values
                if rn not in unconfigured_repos:
                    raise GripTomlError("repo '%s' description specified in config '%s' but it is not one of the repos for that config (repos are %s)"%(rn, self.name, str_keys(unconfigured_repos)))
                repo_descs_just_for_config[rn] = values.Get(rn)
                pass
            pass
        for (rn, urd) in unconfigured_repos.items():
            urd_values = None
            if rn in repo_descs_just_for_config: urd_values = repo_descs_just_for_config[rn]
            self.repos[rn] = RepositoryDescriptorInConfig(self, urd, values=urd_values)
            pass
        pass
    #f build_stages_from_values
    def build_stages_from_values(self) -> None:
        """
        Build a stages dictionary
        it must have <stage name> -> Stage for every stage name in the global stages
        as well as those locally for the config
        """
        stage_values :Dict[str,Optional[TomlDictValues]] = {}
        self.grip_repo_desc.base.add_log_string("adding stages")
        stages : Dict[str,Optional[StageDescriptor]] = {}
        for s in self.grip_repo_desc.iter_stages():
            sn = s.get_name()
            stage_values[sn] = None
            stages[sn] = s
            pass
        if self.values.stage is not None:
            for sn in self.values.stage.Get_other_attrs():
                stage_values[sn] = self.values.stage.Get(sn)
                if sn not in stages: stages[sn] = None
                pass
            pass
        self.stages = {}
        for sn in stage_values.keys():
            self.grip_repo_desc.base.add_log_string("adding stage %s"%(sn))
            stage = stages[sn]
            if stage is None:
                self.stages[sn] = StageDescriptor(grip_repo_desc=self.grip_repo_desc, name=sn, values=stage_values[sn])
                pass
            else:
                self.stages[sn] = stage.clone(values=stage_values[sn])
                pass
            pass
        pass
    #f resolve_git_urls
    def resolve_git_urls(self, grip_git_url:GitUrl) -> None:
        """
        Resolve all relative (and those using environment variables?) git urls
        """
        for (n,r) in self.repos.items():
            r.resolve_git_url(grip_git_url)
            pass
        pass
    #f get_name
    def get_name(self) -> str:
        """
        Get name string for this configuration
        """
        return self.name
    #f get_stage - used by repo to build makefiles
    def get_stage(self, stage_name:str) -> Optional[StageDescriptor]:
        """
        Get dictionary of stage name -> Stage
        """
        if stage_name in self.stages: return self.stages[stage_name]
        return None
    #f get_repo
    def get_repo(self, repo_name:str, error_on_not_found:bool=True) -> Optional[RepositoryDescriptorInConfig]:
        if repo_name not in self.repos:
            if not error_on_not_found: return None
            raise GripTomlError("Repository '%s' not know in grip configuration '%s'"%(repo_name, self.name))
        return self.repos[repo_name]
    #f iter_repos - iterate over repos in config, each is RepositoryDescriptor instance
    def iter_repos(self) -> Iterable[RepositoryDescriptorInConfig]:
        for n in self.repos:
            self.grip_repo_desc.base.add_log_string("iter repos yield %s"%(n))
            yield self.repos[n]
            pass
        pass
    #f iter_stages - iterate over stages in config, each is Stage instance
    def iter_stages(self) -> Iterable[StageDescriptor]:
        for n in self.stages:
            yield self.stages[n]
            pass
        pass
    #f validate
    def validate(self, error_handler:ErrorHandler=None) -> None:
        for r in self.iter_repos():
            r.validate(error_handler=error_handler)
            pass
        for sn,s in self.stages.items():
            s.validate(self,error_handler=error_handler)
            pass
        pass
    #f has_stage - used by Stage to validate for a repo
    def has_stage(self, stage_name:str) -> bool:
        return stage_name in self.stages
    #f resolve
    def resolve(self, error_handler:ErrorHandler=None) -> None:
        """
        Run through repo descriptions and replace grip environment as required
        """
        self.env.resolve(error_handler=error_handler)
        for r in self.iter_repos():
            r.resolve(self.env, error_handler=error_handler)
            pass
        for (n,s) in self.stages.items():
            s.resolve(self.env, error_handler=error_handler)
            pass
        pass
    #f get_env_dict
    def get_env(self) -> EnvDict:
        return self.env.as_dict(include_parent=True)
    #f get_env_as_makefile_strings
    def get_env_as_makefile_strings(self) -> MakefileStrings:
        return self.env.as_makefile_strings(include_parent=True)
    #f get_doc_string
    def get_doc_string(self) -> str:
        """
        Get documentation string for this configuration
        """
        r = "Undocumented"
        if self.doc is not None: r = self.doc.strip()
        return r
    #f get_doc
    def get_doc(self) -> Documentation:
        """
        Return documentation = list of <string> | (name * documentation)
        List should include this configuration and all its repos
        List should always start with (None, repo.doc) if there is repo doc
        """
        r    : Documentation = self.grip_repo_desc.get_doc(include_configs=False)
        blah : Documentation = [self.get_doc_string()]
        r_stage_names = list(self.stages.keys())
        r_stage_names.sort()
        if len(r_stage_names)>0:
            stages_string = "Stages:"
            for rsn in r_stage_names:
                action_string = ""
                if self.stages[rsn].is_action():action_string = "*"
                stages_string += " %s%s"%(action_string,rsn)
                pass
            blah.append(stages_string)
            for sn in r_stage_names:
                stage_doc = self.stages[sn].get_doc_string()
                if stage_doc !="": blah.append(("Stage %s"%sn,[stage_doc]))
                pass
            pass
        for (rn,repo) in self.repos.items():
            blah.append(("Repo '%s'"%rn,repo.get_doc()))
            pass
        r.append(("Configuration '%s'"%self.name,blah))
        return r
    #f fold_config_stages
    def fold_config_stages(self, acc:Any, callback_fn:Callable[[Any,Any,StageDescriptor],Any]) -> Any:
        for s in self.iter_stages():
            acc = callback_fn(acc, None, s)
            pass
        return acc
    #f fold_repo_stages
    def fold_repo_stages(self, acc:Any, callback_fn:Callable[[Any,RepositoryDescriptorInConfig,StageDescriptor],Any]) -> Any:
        for r in self.iter_repos():
            acc = r.fold_repo_stages(acc, callback_fn)
            pass
        return acc
    #f write_makefile_entries
    def write_makefile_entries(self, f:IO[str], verbose:Any) -> None:
        for stage in self.iter_stages():
            stage.write_makefile_entries(f, verbose)
            pass
        for r in self.iter_repos():
            for stage in r.iter_stages():
                stage.write_makefile_entries(f, verbose)
                pass
            pass
        pass
    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        acc = pp(acc, "config.%s:" % (self.name))
        for (n,r) in self.repos.items():
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent+1)
            acc = r.prettyprint(acc, ppr)
            pass
        for name in self.stages:
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent+1)
            acc = self.stages[name].prettyprint(acc,ppr)
            pass
        return acc
    #f __str__
    def __str__(self) -> str:
        def pp(acc:str,s:str,indent:int=0)->str: return acc + ("  "*indent) + s + "\n"
        return cast(str,self.prettyprint("", pp))
    #f All done
    pass

