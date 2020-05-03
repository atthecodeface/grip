#a Imports
import os, sys, re, copy
from .tomldict import TomlDict, TomlDictParser
from .exceptions import *
from .env import GripEnv, EnvTomlDict
from .git_repo_desc import RepoDescTomlDict, GitRepoDesc
from .stage import StageTomlDict, GitRepoStageDependency, GitRepoStageDesc

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

#c GripConfig - a set of GripRepoDesc's for a configuration of the grip repo
class GripConfig(object):
    """
    A GripConfig describes a configuration of a grip repo.

    A grip repo configuration is a set of git repos, and for each git repo the relevant commands and dependencies
    to install, test_install, make, run, test and precommit

    """
    repos = {} # dictionary of <repo name> : <GitRepoDesc instance>
    #f __init__
    def __init__(self, name, grip_repo_desc):
        self.name = name
        self.doc = None
        self.grip_repo_desc = grip_repo_desc
        self.env = GripEnv(name="config '%s'"%self.name,
                           parent=grip_repo_desc.env )
        self.repos = {}
        self.stages = {}
        for r in self.grip_repo_desc.base_repos:
            self.repos[r] = self.grip_repo_desc.repos[r].clone()
            pass
        pass
    #f build_from_values
    def build_from_values(self, values):
        """
        values is a SpecificConfigTomlDict._values

        Hence it has a .doc, .repos (possibly None) and other attributes that should be <reponame> of type RepoDescTomlDict._values
        """
        values.Set_obj_properties(self, {"doc"})
        self.env.build_from_values(values.env)
        if values.repos is None:values.repos={}
        if values.stage is not None:
            for stage in values.stage.Get_other_attrs():
                stage_values = values.stage.Get(stage)
                self.stages[stage] = GitRepoStageDesc(self.grip_repo_desc, stage, stage_values)
                pass
            pass
        for r in values.repos:
            if r not in self.grip_repo_desc.repos:raise GripTomlError("repo '%s' specified in config '%s' but it is not defined in the file"%(r, self.name))
            self.repos[r] = self.grip_repo_desc.repos[r].clone()
            pass
        for r in values.Get_other_attrs(): # These must be RepoDescTomDict._values
            if r not in self.repos:raise GripTomlError("repo '%s' description specified in config '%s' but it is not one of the repos for that config (repos are %s)"%(r, self.name, str_keys(self.repos)))
            repo_desc = values.Get(r)
            self.repos[r] = GitRepoDesc(r, values=repo_desc, parent=self.repos[r], grip_repo_desc=self.grip_repo_desc)
            pass
        for r in self.iter_repos():
            r.set_grip_config(self)
            pass
        pass
    #f resolve_git_urls
    def resolve_git_urls(self, grip_git_url):
        """
        Resolve all relative (and those using environment variables?) git urls
        """
        for (n,r) in self.repos.items():
            r.resolve_git_url(grip_git_url)
            pass
        pass
    #f get_repo
    def get_repo(self, repo_name, error_on_not_found=True):
        if repo_name not in self.repos:
            if not error_on_not_found: return None
            raise GripTomlError("Repository '%s' not know in grip configuration '%s'"%(repo_name, self.name))
        return self.repos[repo_name]
    #f iter_repos - iterate over repos in config, each is GitRepoDesc instance
    def iter_repos(self):
        for n in self.repos:
            yield self.repos[n]
            pass
        pass
    #f validate
    def validate(self, error_handler=None):
        for r in self.iter_repos():
            r.validate(error_handler=error_handler)
            pass
        for sn,s in self.stages.items():
            s.validate(self,error_handler=error_handler)
            pass
        pass
    #f resolve
    def resolve(self, error_handler=None):
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
    def get_env(self):
        return self.env.as_dict(include_parent=True)
    #f get_env_as_makefile_strings
    def get_env_as_makefile_strings(self):
        return self.env.as_makefile_strings(include_parent=True)
    #f get_name
    def get_name(self):
        """
        Get name string for this configuration
        """
        return self.name
    #f get_doc_string
    def get_doc_string(self):
        """
        Get documentation string for this configuration
        """
        r = "Undocumented"
        if self.doc is not None: r = self.doc.strip()
        r_stages = []
        for sn in self.get_global_stage_names():
            r_stages.append(sn)
            pass
        for (sn,s) in self.stages.items():
            if sn not in r_stages:
                r_stages.append(sn)
                pass
            pass
        r_stages.sort()
        r += "\nStages: %s"%(" ".join(r_stages))
        return r
    #f get_doc
    def get_doc(self):
        """
        Return list of (name, documentation) strings
        List should include this configuration and all its repos
        List should always start with (None, repo.doc) if there is repo doc
        """
        r = self.grip_repo_desc.get_doc(include_configs=False)
        r.append(("Configuration '%s'"%self.name,self.get_doc_string()))
        for (rn,repo) in self.repos.items():
            r.append(("Repo '%s'"%rn,repo.get_doc_string()))
            pass
        return r
    #f get_global_stage_names
    def get_global_stage_names(self):
        return self.grip_repo_desc.get_stages().keys()
    #f get_global_stages
    def get_global_stages(self):
        return self.grip_repo_desc.get_stages()
    #f fold_repo_stages
    def fold_repo_stages(self, acc, callback_fn):
        for r in self.iter_repos():
            acc = r.fold_repo_stages(acc, callback_fn)
            pass
        return acc
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "config.%s:" % (self.name))
        for (n,r) in self.repos.items():
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent+1)
            acc = r.prettyprint(acc, ppr)
            pass
        for name in self.stages:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent+1)
            acc = self.stages[name].prettyprint(acc,ppr)
            pass
        return acc
    #f __str__
    def __str__(self):
        def pp(acc,s,indent=0): return acc + ("  "*indent) + s + "\n"
        return self.prettyprint("", pp)
    #f All done
    pass

