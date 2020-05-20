#a Imports
from pathlib import Path

from typing import Optional, Type, Dict, List, Union, Any, Tuple, Sequence, Set, Iterable, Callable
from ..tomldict import TomlDict, TomlDictParser, TomlDictValues
from ..git import Url as GitUrl
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict

from typing import TYPE_CHECKING
from ..types import PrettyPrinter, Documentation, MakefileStrings
if TYPE_CHECKING:
    from ..descriptor import ConfigurationDescriptor
    from ..descriptor import GripDescriptor
    from ..grip import Toplevel
    from ..workflow import Workflow

class RepoDescTomlDict(TomlDict):
    """A repo description: where it is, which VCS it uses, pull methodology, push methodology, where it exists,
    and what to do with it for various grip stages
    """
    url       = TomlDictParser.from_dict_attr_value(str)
    workflow  = TomlDictParser.from_dict_attr_value(str)
    branch    = TomlDictParser.from_dict_attr_value(str)
    path      = TomlDictParser.from_dict_attr_value(str)
    shallow   = TomlDictParser.from_dict_attr_bool()
    env       = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
    doc       = TomlDictParser.from_dict_attr_value(str)
    Wildcard  = TomlDictParser.from_dict_attr_dict(StageTomlDict)
    pass

#c DescriptorValues - namespace that contains values from the TomlDict
class DescriptorValues(object):
    url      = None
    branch   = None
    path     = None
    workflow = None
    git_url  = None
    shallow  = None
    env      = None
    doc      = None
    grip_config = None
    inherited_properties = ["url", "branch", "path", "workflow", "git_url", "shallow", "env", "doc"]
    #f __init__
    def __init__(self, values:Optional[TomlDictValues], clone:Optional['DescriptorValues']):
        if values is not None:
            values.Set_obj_properties(self, values.Get_fixed_attrs())
            pass
        def set_current_or_parent(k:str) -> None:
            if getattr(self,k) is None: setattr(self,k,getattr(clone,k))
            pass
        if clone is not None:
            for k in self.inherited_properties:
                set_current_or_parent(k)
                pass
            pass
        pass

#c DescriptorBase - a descriptor of a repository within the grip description
class DescriptorBase(object):
    """
    """
    #t types and default values of instance properties
    values : DescriptorValues
    name : str
    cloned_from : Optional['Descriptor']
    url      : str = "<undefined_url>"
    _path    : Path
    shallow  : bool
    branch   : Optional[str]=None
    env      : GripEnv
    doc      : Optional[str]=None
    stages   : Dict[str,StageDescriptor]
    workflow : Type['Workflow']
    _is_resolved : bool = False
    #f __init__
    def __init__(self, name:str, grip_repo_desc:'GripDescriptor'):
        """
        values must be a RepoDescTomlDict._values
        """
        self.name   = name
        self.grip_repo_desc = grip_repo_desc
        pass
    #f path
    def path(self) -> Path:
        assert self._is_resolved
        return Path(self._path)
    #f get_doc_string
    def get_doc_string(self) -> str:
        """
        Get documentation string for this configuration
        """
        r = "Undocumented"
        if self.doc is not None: r = self.doc
        return r
    #f add_stage_names_to_set
    def add_stage_names_to_set(self, s:Set[str]) -> None:
        for k in self.stages:
            s.add(k)
            pass
        pass
    #f get_repo_stage
    def get_repo_stage(self, stage_name:str, error_on_not_found:bool=True) -> Optional[StageDescriptor]:
        if stage_name not in self.stages:
            if not error_on_not_found: return None
            raise GripTomlError("Stage '%s' not known in repository '%s'"%(stage_name, self.name))
        return self.stages[stage_name]
    #f iter_stages
    def iter_stages(self) -> Iterable[StageDescriptor]:
        for (sn,s) in self.stages.items():
            yield(s)
            pass
        pass
    #f is_shallow
    def is_shallow(self) -> bool:
        if self.shallow is not None:
            return self.shallow
        return False
    #f get_env_as_makefile_strings
    def get_env_as_makefile_strings(self) -> MakefileStrings:
        return self.env.as_makefile_strings(include_parent=False)
    #f All done
    pass


#c Descriptor - a descriptor of a repository within the grip description
class Descriptor(DescriptorBase):
    """
    """
    #f __init__
    def __init__(self, name:str, grip_repo_desc:'GripDescriptor', values:Optional[TomlDictValues]=None):
        """
        values must be a RepoDescTomlDict._values
        """
        DescriptorBase.__init__(self, name=name, grip_repo_desc=grip_repo_desc)
        self.stages = {}
        self.values = DescriptorValues(values, None)
        if values is not None:
            for stage_name in values.Get_other_attrs():
                stage_values = values.Get(stage_name)
                self.stages[stage_name] = StageDescriptor(grip_repo_desc=self.grip_repo_desc,
                                                          name=stage_name,
                                                          repo=None,
                                                          values=stage_values)
                pass
            pass
        if self.values.url is None: raise GripTomlError("repo '%s' has no url to clone from"%(self.name))
        pass

    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        acc = pp(acc, "repo.%s:" % (self.name))
        acc = pp(acc, "url(orig):   %s" % (self.url), indent=1)
        if self._is_resolved:
            acc = pp(acc, "path:        %s" % (str(self._path)), indent=1)
            pass
        if self.branch  is not None: acc = pp(acc, "branch:      %s" % (self.branch), indent=1)
        for name in self.stages:
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent+1)
            acc = self.stages[name].prettyprint(acc,ppr)
            pass
        return acc
#c DescriptorInConfig - descriptor instantiated in a configuration
class DescriptorInConfig(DescriptorBase):
    """
    """
    git_url  : GitUrl
    grip_config : 'ConfigurationDescriptor'
    #f __init__
    def __init__(self, grip_config:'ConfigurationDescriptor', clone:Descriptor, values:Optional[TomlDictValues]=None):
        """
        values must be a RepoDescTomlDict._values
        """
        DescriptorBase.__init__(self, name=clone.name, grip_repo_desc=clone.grip_repo_desc)
        self.cloned_from = clone
        self.grip_config = grip_config
        self.values = DescriptorValues(values, clone.values)
        self.stages = {}
        if values is not None:
            for stage_name in values.Get_other_attrs():
                stage_values = values.Get(stage_name)
                self.stages[stage_name] = StageDescriptor(grip_repo_desc=self.grip_repo_desc, name=stage_name, repo=self, values=stage_values)
                pass
            pass
        for (n,s) in clone.stages.items():
            if n not in self.stages:
                self.stages[n] = s.clone(grip_repo_desc=self.grip_repo_desc, repo=self)
                pass
            pass
        pass
    #f validate
    def validate(self, check_stage_dependencies:bool, error_handler:ErrorHandler=None) -> None:
        if self.values.workflow is None:
            self.workflow = self.grip_repo_desc.workflow
            pass
        else:
            self.workflow = self.grip_repo_desc.validate_workflow(self.values.workflow, self.name)
            pass
        for (n,s) in self.stages.items():
            s.validate(self.grip_config, check_dependencies=check_stage_dependencies, error_handler=error_handler)
            pass
        pass
    #f get_doc
    def get_doc(self) -> Documentation:
        """
        Return documentation = list of <string> | (name * documentation)
        Get documentation
        """
        r : Documentation = [self.get_doc_string()]
        r_src = ""
        if hasattr(self,"_path"): r_src += "locally at '%s'" % (str(self._path))
        if self.url     is not None: r_src += " remote url(orig) '%s'" % (self.url)
        r_src += " remote url(parsed) '%s'" % (self.git_url.as_string())
        if self.branch  is not None: r_src += " branch '%s'" % (self.branch)
        r.append(r_src)
        r_stages = []
        for (sn,s) in self.stages.items():
            r_stages.append(sn)
            pass
        r_stages.sort()
        if len(r_stages)>0:
            r.append("Stages: %s"%(" ".join(r_stages)))
            pass
        return r
    #f resolve
    def resolve(self, env:GripEnv, resolve_fully:bool=True, error_handler:ErrorHandler=None) -> None:
        """
        Resolve the strings in the repo description and its stages, using the repo configuration's environment

        If resolve_fully is True then all the environment must resolve
        If resolve_fully is False then the URL, path and branch must resolve
        """
        self.grip_repo_desc.base.add_log_string("Resolve repo '%s' in config '%s'"%(self.name, self.grip_config.name))
        self.env = GripEnv(name="repo %s"%self.name, parent=env)
        self.env.build_from_values(self.values.env)
        url     = self.env.substitute(self.values.url, finalize=True, error_handler=error_handler)
        if url is None:
            raise GripTomlError("for repo '%s' has unknown url '%s'"%(self.name, self.values.url))
        self.url = url
        try:
            self.git_url = GitUrl(self.url)
            pass
        except:
            raise GripTomlError("for repo '%s' could not parse git url '%s'"%(self.name, self.url))

        self.branch  = self.env.substitute(self.values.branch, finalize=True, error_handler=error_handler)
        self._path = Path(self.git_url.repo_name)
        if self.values.path is not None:
            self._path = Path(self.env.substitute(self.values.path, finalize=True, error_handler=error_handler))
            pass

        if self.values.shallow is None:
            self.shallow = False
            pass
        else:
            self.shallow = self.values.shallow
            pass

        self.doc     = self.values.doc

        self.env.add_values({"GRIP_REPO_PATH":"@GRIP_ROOT_PATH@/"+str(self._path)})
        if resolve_fully:
            self.env.resolve(error_handler=error_handler)
            for (n,s) in self.stages.items():
                s.resolve(self.env, error_handler=error_handler)
                pass
            pass
        # print("Resolve %s:%s:%s:%s"%(self,self.name,self.url,self.git_url))
        self._is_resolved = True
        pass
    #f get_git_url
    def get_git_url(self) -> GitUrl:
        """
        """
        assert self._is_resolved
        return self.git_url
    #f get_git_url_string
    def get_git_url_string(self) -> str:
        """
        """
        assert self._is_resolved
        return self.git_url.as_string()
    #f resolve_git_url
    def resolve_git_url(self, grip_git_url:GitUrl) -> None:
        """
        Resolve relative (and those using environment variables?) git urls
        """
        assert self._is_resolved
        if self.git_url.is_leaf():
            self.git_url.make_relative_to(abs_url=grip_git_url)
            pass
        pass
    #f fold_repo_stages
    def fold_repo_stages(self, acc:Any, callback_fn:Callable[[Any,'DescriptorInConfig',StageDescriptor],Any])->Any:
        for (sn,s) in self.stages.items():
            acc = callback_fn(acc, self, s)
            pass
        return acc

    #f prettyprint
    def prettyprint(self, acc:Any, pp:PrettyPrinter) -> Any:
        acc = pp(acc, "repo.%s:" % (self.name))
        acc = pp(acc, "cfg:         %s" % (self.grip_config.name), indent=1)
        acc = pp(acc, "url(orig):   %s" % (self.url), indent=1)
        if self._is_resolved:
            acc = pp(acc, "url(parsed)  %s" % (self.git_url.as_string()), indent=1)
            acc = pp(acc, "path:        %s" % (str(self._path)), indent=1)
        if self.branch  is not None: acc = pp(acc, "branch:      %s" % (self.branch), indent=1)
        for name in self.stages:
            def ppr(acc:Any, s:str, indent:int=0) -> Any:
                return pp(acc, s, indent=indent+1)
            acc = self.stages[name].prettyprint(acc,ppr)
            pass
        return acc
