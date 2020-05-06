#a Imports
import os, sys, re, copy
from .tomldict import TomlDict, TomlDictParser
from .exceptions import *
from .env import GripEnv, EnvTomlDict
from .git_repo_desc import RepoDescTomlDict, GitRepoDesc
# from .stage import Dependency as StageDependency
from .stage import Descriptor as StageDescriptor
from .stage import StageTomlDict

#a Useful functions
def str_keys(d):
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
        # Build repos before stages, as stages refer to the repos
        self.build_repos_from_values(values)
        self.build_stages_from_values(values)
        pass
    #f build_repos_from_values
    def build_repos_from_values(self, values):
        """
        """
        if values.repos is None:values.repos={}
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
    #f build_stages_from_values
    def build_stages_from_values(self, values):
        """
        Build a stages dictionary
        it must have <stage name> -> Stage for every stage name in the global stages
        as well as those locally for the config
        """
        stage_values = {}
        if values.stage is not None:
            for stage in values.stage.Get_other_attrs():
                stage_values[stage] = values.stage.Get(stage)
                pass
            pass
        for s in self.grip_repo_desc.iter_stages():
            sn = s.get_name()
            if sn not in stage_values:
                stage_values[sn] = None
                pass
            pass
        self.stages = {}
        for sn in stage_values.keys():
            self.stages[sn] = self.grip_repo_desc.get_stage(sn)
            if self.stages[sn] is None:
                self.stages[sn] = StageDescriptor(grip_repo_desc=self.grip_repo_desc, name=sn, values=stage_values[sn])
                pass
            else:
                self.stages[sn] = self.stages[sn].clone(values=stage_values[sn])
                pass
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
    #f iter_stages - iterate over stages in config, each is Stage instance
    def iter_stages(self):
        for n in self.stages:
            yield self.stages[n]
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
    #f has_stage - used by Stage to validate for a repo
    def has_stage(self, stage_name):
        return stage_name in self.stages
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
    #f get_stage - used by repo to build makefiles
    def get_stage(self, stage_name):
        """
        Get dictionary of stage name -> Stage
        """
        if stage_name in self.stages: return self.stages[stage_name]
        return None
    #f get_doc_string
    def get_doc_string(self):
        """
        Get documentation string for this configuration
        """
        r = "Undocumented"
        if self.doc is not None: r = self.doc.strip()
        return r
    #f get_doc
    def get_doc(self):
        """
        Return documentation = list of <string> | (name * documentation)
        List should include this configuration and all its repos
        List should always start with (None, repo.doc) if there is repo doc
        """
        r = self.grip_repo_desc.get_doc(include_configs=False)
        blah = [self.get_doc_string()]
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
                if stage_doc is not None: blah.append(("Stage %s"%sn,[stage_doc]))
                pass
            pass
        for (rn,repo) in self.repos.items():
            blah.append(("Repo '%s'"%rn,repo.get_doc()))
            pass
        r.append(("Configuration '%s'"%self.name,blah))
        return r
    #f fold_config_stages
    def fold_config_stages(self, acc, callback_fn):
        for s in self.iter_stages():
            acc = callback_fn(acc, None, s)
            pass
        return acc
    #f fold_repo_stages
    def fold_repo_stages(self, acc, callback_fn):
        for r in self.iter_repos():
            acc = r.fold_repo_stages(acc, callback_fn)
            pass
        return acc
    #f write_makefile_entries
    def write_makefile_entries(self, f, verbose):
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

