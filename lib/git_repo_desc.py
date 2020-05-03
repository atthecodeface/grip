#a Imports
import os, sys, re, copy
import toml
from .tomldict import TomlDict, TomlDictParser
from .git import GitRepo
from .workflows import workflows
from .exceptions import *
from .env import GripEnv, EnvTomlDict
from .stage import StageTomlDict, GitRepoStageDesc

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

#c GitRepoDesc - a grip repo module (where it sits in the grip repo, its source url/branch etc, and its stages)
class GitRepoDesc(object):
    """
    A GitRepoDesc is a simple object containing the data describing a git repo that is part of a grip repo

    Each GitRepoDesc should have an entry repo.<name> as a table of <property>:<value> in the grip.toml file

    Possibly this can include <install>

    A GitRepoDesc may have a changeset associated with it from a .grip/state file

    A GitRepoDesc may be read-only; push-to-integration; push-to-patch?; merge?

    Possibly it should have a default dictionary of <stage> -> <GitRepoStageDesc>
    """
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
    def __init__(self, name, grip_repo_desc, values=None, parent=None):
        """
        values must be a RepoDescTomlDict._values
        """
        self.name   = name
        self.parent = parent
        self.grip_repo_desc = grip_repo_desc
        self.stages = {}
        if values is not None:
            values.Set_obj_properties(self, values.Get_fixed_attrs())
            pass
        if values is not None:
            for stage in values.Get_other_attrs():
                stage_values = values.Get(stage)
                self.stages[stage] = GitRepoStageDesc(self.grip_repo_desc, stage, git_repo_desc=self, values=stage_values)
                pass
            pass
        if parent is not None:
            def set_current_or_parent(k):
                if getattr(self,k) is None: setattr(self,k,getattr(parent,k))
                pass
            for k in self.inherited_properties:
                set_current_or_parent(k)
                pass
            for (n,s) in parent.stages.items():
                if n not in self.stages:
                    self.stages[n] = s.clone()
                    pass
                pass
            pass
        if self.workflow is None: self.workflow = grip_repo_desc.workflow
        if self.url      is None: raise GripTomlError("repo '%s' has no url to clone from"%(self.name))
        pass
    #f clone
    def clone(self):
        c = self.__class__(name=self.name, values=None, grip_repo_desc=self.grip_repo_desc, parent=self)
        c.parent = self.parent
        return c
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
    def get_path(self):
        return self.path
    #f get_git_url
    def get_git_url(self):
        """
        """
        return self.git_url
    #f get_git_url_string
    def get_git_url_string(self):
        """
        """
        return self.git_url.git_url()
    #f get_doc_string
    def get_doc_string(self):
        """
        Get documentation string for this configuration
        """
        r = "Undocumented"
        if self.doc is not None: r = self.doc
        return r
    #f get_doc
    def get_doc(self):
        """
        Return documentation = list of <string> | (name * documentation)
        Get documentation
        """
        r = [self.get_doc_string()]
        r_src = ""
        if self.path    is not None: r_src += "locally at '%s'" % (self.path)
        if self.git_url is not None: r_src += " remote url '%s'" % (self.git_url.git_url())
        elif self.url is not None:   r_src += " remote url(orig) '%s'" % (self.url)
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
    def add_stage_names_to_set(self, s):
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
    #f fold_repo_stages
    def fold_repo_stages(self, acc, callback_fn):
        for (sn,s) in self.stages.items():
            acc = callback_fn(acc, self, s)
            pass
        return acc
    #f is_shallow
    def is_shallow(self):
        if self.shallow is not None:
            if self.shallow=="yes" or self.shallow=="true":
                return True
            pass
        return False
    #f validate
    def validate(self, error_handler=None):
        self.workflow = self.grip_repo_desc.validate_workflow(self.workflow, self.name)
        for (n,s) in self.stages.items():
            s.validate(self.grip_config, error_handler=error_handler)
            pass
        pass
    #f resolve
    def resolve(self, env, error_handler=None):
        """
        Resolve the strings in the repo description and its stages, using the repo configuration's environment
        """
        env = GripEnv(name="repo %s"%self.name,
                      parent=env)
        env.build_from_values(self.env)
        self.env = env
        self.url    = self.env.substitute(self.url,     error_handler=error_handler)
        self.path   = self.env.substitute(self.path,    error_handler=error_handler)
        self.branch = self.env.substitute(self.branch,  error_handler=error_handler)
        try:
            self.git_url = GitRepo.parse_git_url(self.url)
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
    def get_env_as_makefile_strings(self):
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

