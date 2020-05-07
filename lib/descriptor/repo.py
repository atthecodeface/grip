#a Imports
from typing import Optional, Type, List, Union, Any, Tuple, Sequence
from ..tomldict import TomlDict, TomlDictParser, TomlDictValues
from ..git import GitRepo, GitUrl
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict

class RepoDescTomlDict(TomlDict):
    """A repo description: where it is, which VCS it uses, pull methodology, push methodology, where it exists,
    and what to do with it for various grip stages
    """
    url       = TomlDictParser.from_dict_attr_value(str)
    workflow  = TomlDictParser.from_dict_attr_value(str)
    branch    = TomlDictParser.from_dict_attr_value(str)
    path      = TomlDictParser.from_dict_attr_value(str)
    shallow   = TomlDictParser.from_dict_attr_value(str)
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
    def __init__(self, values : TomlDictValues, clone : Type['DescriptorValues']):
        if values is not None:
            values.Set_obj_properties(self, values.Get_fixed_attrs())
            pass
        def set_current_or_parent(k):
            if getattr(self,k) is None: setattr(self,k,getattr(clone,k))
            pass
        if clone is not None:
            for k in self.inherited_properties:
                set_current_or_parent(k)
                pass
            pass
        pass

#c Descriptor - a descriptor of a repository within the grip description
class Descriptor(object):
    """
    This is a simple object containing the data describing a git repo that is part of a grip repo

    Each GitRepoDesc should have an entry repo.<name> as a table of <property>:<value> in the grip.toml file

    Possibly this can include <install>

    A GitRepoDesc may have a changeset associated with it from a .grip/state file

    A GitRepoDesc may be read-only; push-to-integration; push-to-patch?; merge?

    Possibly it should have a default dictionary of <stage> -> <StageDescriptor>
    """
    values : DescriptorValues
    name : str
    cloned_from : Optional[Type['Descriptor']]
    url      : Optional[str]
    branch   : Optional[str]
    path     : Optional[str]
    shallow  : int
    env      : GripEnv
    doc      : Optional[str]
    git_url  : GitUrl
    from ..workflow import Workflow
    workflow : Workflow
    # grip_config
    #f __init__
    def __init__(self, name, grip_repo_desc, values=None, clone=None):
        """
        values must be a RepoDescTomlDict._values
        """
        self.name   = name
        self.grip_repo_desc = grip_repo_desc
        self.cloned_from = clone
        self.stages = {}
        clone_values = None
        if clone is not None: clone_values=clone.values
        self.values = DescriptorValues(values, clone_values)
        if values is not None:
            for stage_name in values.Get_other_attrs():
                stage_values = values.Get(stage_name)
                self.stages[stage_name] = StageDescriptor(grip_repo_desc=self.grip_repo_desc, name=stage_name, git_repo_desc=self, values=stage_values)
                pass
            pass
        if clone is not None:
            for (n,s) in clone.stages.items():
                if n not in self.stages:
                    self.stages[n] = s.clone(grip_repo_desc=grip_repo_desc, git_repo_desc=self)
                    pass
                pass
            pass
        if self.values.url      is None: raise GripTomlError("repo '%s' has no url to clone from"%(self.name))
        pass
    #f clone
    def clone(self):
        return self.__class__(name=self.name, values=None, grip_repo_desc=self.grip_repo_desc, clone=self)
    #f set_grip_config
    def set_grip_config(self, grip_config):
        """
        When instantiated in a grip config, this is invoked
        """
        self.grip_config = grip_config
        pass
    #f resolve_git_url
    def resolve_git_url(self, grip_git_url):
        """
        Resolve relative (and those using environment variables?) git urls
        """
        if self.git_url.is_leaf():
            self.git_url.make_relative_to(grip_git_url)
            pass
        pass
    #f get_path
    def get_path(self) -> str:
        assert self.path is not None
        return self.path
    #f get_git_url
    def get_git_url(self):
        """
        """
        return self.git_url
    #f get_git_url_string
    def get_git_url_string(self) -> str:
        """
        """
        assert self.git_url is not None
        return self.git_url.as_string()
    #f get_doc_string
    def get_doc_string(self) -> str:
        """
        Get documentation string for this configuration
        """
        r = "Undocumented"
        if self.doc is not None: r = self.doc
        return r
    #f get_doc
    def get_doc(self) -> Sequence[ Union [ str, List[ Tuple[str, Any]]]]:
        """
        Return documentation = list of <string> | (name * documentation)
        Get documentation
        """
        r = [self.get_doc_string()]
        r_src = ""
        if self.path    is not None: r_src += "locally at '%s'" % (self.path)
        if self.url     is not None: r_src += " remote url(orig) '%s'" % (self.url)
        if self.git_url is not None: r_src += " remote url(parsed) '%s'" % (self.git_url.as_string())
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
    #f add_stage_names_to_set
    def add_stage_names_to_set(self, s:set):
        for k in self.stages:
            s.add(k)
            pass
        pass
    #f get_repo_stage
    def get_repo_stage(self, stage_name, error_on_not_found=True):
        if stage_name not in self.stages:
            if not error_on_not_found: return None
            raise GripTomlError("Stage '%s' not known in repository '%s'"%(stage_name, self.name))
        return self.stages[stage_name]
    #f iter_stages
    def iter_stages(self):
        for (sn,s) in self.stages.items():
            yield(s)
            pass
        pass
    #f fold_repo_stages
    def fold_repo_stages(self, acc, callback_fn):
        for (sn,s) in self.stages.items():
            acc = callback_fn(acc, self, s)
            pass
        return acc
    #f is_shallow
    def is_shallow(self) -> bool:
        if self.shallow is not None:
            if self.shallow=="yes" or self.shallow=="true":
                return True
            pass
        return False
    #f validate
    def validate(self, error_handler=None):
        if self.values.workflow is None:
            self.workflow = self.grip_repo_desc.workflow
            pass
        else:
            self.workflow = self.grip_repo_desc.validate_workflow(self.values.workflow, self.name)
            pass
        for (n,s) in self.stages.items():
            s.validate(self.grip_config, error_handler=error_handler)
            pass
        pass
    #f resolve
    def resolve(self, env, error_handler=None):
        """
        Resolve the strings in the repo description and its stages, using the repo configuration's environment
        """
        self.env = GripEnv(name="repo %s"%self.name, parent=env)
        self.env.build_from_values(self.values.env)
        self.url     = self.env.substitute(self.values.url,      error_handler=error_handler)
        self.branch  = self.env.substitute(self.values.branch,   error_handler=error_handler)
        self.shallow = self.env.substitute(self.values.shallow,  error_handler=error_handler)
        self.path    = self.values.path
        self.doc     = self.values.doc
        try:
            self.git_url = GitUrl(self.url)
            pass
        except:
            raise GripTomlError("for repo '%s' could not parse git url '%s'"%(self.name, self.url))

        if self.path is None:
            self.path = self.git_url.repo_name
            pass

        self.env.add_values({"GRIP_REPO_PATH":"@GRIP_ROOT_PATH@/"+self.path})
        self.env.resolve(error_handler=error_handler)
        for (n,s) in self.stages.items():
            s.resolve(self.env, error_handler=error_handler)
            pass
        # print("Resolve %s:%s:%s:%s"%(self,self.name,self.url,self.git_url))
        pass
    #f get_env_as_makefile_strings
    def get_env_as_makefile_strings(self) -> List[Tuple[str,str]]:
        return self.env.as_makefile_strings(include_parent=False)
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "repo.%s:" % (self.name))
        if self.url     is not None: acc = pp(acc, "url(orig):   %s" % (self.url), indent=1)
        if self.git_url is not None: acc = pp(acc, "url(parsed): %s" % (self.git_url.git_url()), indent=1)
        if self.branch  is not None: acc = pp(acc, "branch:      %s" % (self.branch), indent=1)
        if self.path    is not None: acc = pp(acc, "path:        %s" % (self.path), indent=1)
        for name in self.stages:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent+1)
            acc = self.stages[name].prettyprint(acc,ppr)
            pass
        return acc
    #f All done
    pass

