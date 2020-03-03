#a Imports
import os, sys, re, toml, copy
# from lib.hookable import Hookable
# import lib.utils as utils

#a Classes
#c TomlDict
def type_str(t):
    if t==str:return "string"
    if t==int:return "integer"
    if t==list:return "list"
    if hasattr(t,"__class__"): return str(t.__class__) #.__name__
    return str(t)
class TomlError(Exception):
    def __init__(self, where, reason):
        self.where = where
        self.reason = reason
        pass
    def __str__(self):
        return "%s %s"%(self.where, self.reason)
        pass
    pass
class TomlDict(object):
    """
    attributes can be types, or 
    """
    Wildcard = None
    class _values(object):
        def __init__(self, cls, parent):
            self._dict_class = cls
            self._parent = parent
            self._other_attrs = []
            pass
        def Add_other_attr(self, a, v):
            self._other_attrs.append(a)
            setattr(self, a, v)
            pass
        def Get_other_attrs(self):
            return self._other_attrs
        def Get(self, a):
            return getattr(self, a)
        def Get_attr_dict(self):
            attrs = self._dict_class._toml_fixed_attrs()
            attrs += self._other_attrs
            r = {}
            for a in attrs:
                r[a] = getattr(self,a)
                pass
            return r
        def Prettyprint(self, prefix=""):
            avs = self.Get_attr_dict()
            for (x,value) in avs.items():
                if isinstance(value,TomlDict._values):
                    value.Prettyprint(prefix = "%s.%s"%(prefix,x))
                    pass
                else:
                    print("%s.%s: %s"%(prefix,x,str(value)))
                    pass
                pass
            pass
        pass
    @classmethod
    def _toml_fixed_attrs(cls):
        attrs = dir(cls)
        v = [x for x in attrs if ((x[0]>='a') and (x[0]<='z'))]
        return v
    def __init__(self, client):
        self.__client = client
        pass
class TomlDictParser(object):
    """
    """
    @staticmethod
    def identity_fn(s,p,m,x):
        return x
    @staticmethod
    def from_dict_attr_value(t, fn=None):
        if fn==None: fn=TomlDictParser.identity_fn
        def f(self, parent, msg, value):
            if type(value)!=t: raise TomlError(msg, "Expected %s but got '%s'"%(type_str(t),str(value)))
            return fn(self, parent, msg, value)
        return f
    @staticmethod
    def from_dict_attr_list(t, fn=None):
        if fn==None: fn=TomlDictParser.identity_fn
        def f(self, parent, msg, values):
            if type(values)!=list: raise TomlError(msg, "Expected list of %s but got '%s'"%(str(t),str(values)))
            result = []
            for v in values:
                if type(v)!=t: raise TomlError(msg, "Expected %s but got '%s'"%(type_str(t),str(v)))
                result.append(fn(self, parent, msg, v))
                pass
            return result
        return f
    @staticmethod
    def from_dict_attr_dict(t, fn=None):
        """
        t must be a subclass of TomlDict
        """
        if fn==None: fn=TomlDictParser.identity_fn
        def f(self, parent, msg, values):
            if not isinstance(values,dict): raise TomlError(msg, "Expected dictionary but got '%s'"%(str(values)))
            return TomlDictParser.from_dict(t, parent, msg, values)
        return f
    @staticmethod
    def from_dict(cls, handle, msg, d):
        values = cls._values(cls, handle)
        attrs = cls._toml_fixed_attrs()
        rtd = copy.deepcopy(d)
        for x in attrs:
            if x in rtd:
                values_fn = getattr(cls,x)
                setattr(values, x, values_fn(values, handle, "%s.%s"%(msg,x), rtd[x]))
                del(rtd[x])
                pass
            else:
                setattr(values, x, None)
            pass
        if cls.Wildcard is not None:
            for x in rtd:
                v = cls.Wildcard(values, handle, "%s.%s"%(msg,x), rtd[x])
                values.Add_other_attr(x,v)
                pass
            rtd = {}
            pass
        if len(rtd)>0:
            r = []
            for a in rtd.keys(): r.append(a)
            raise TomlError(msg, "Unparsed keys '%s'"%(" ".join(r)))
        return values
    
#c GitRepoStageDesc
class GitRepoStageDesc(object):
    """
    A GitRepoStageDesc has the data for a particular installation or build mechanism and dependencies for a git repo

    It
    """
    # stage = None # Install/test_install/precommit/?
    # git_repo_desc = None # Git repo descr this is the <stage> of
    wd   = None # Working directory to execute <exec> in (relative to repo desc path)
    exec = None # Shell script to execute to perform the stage
    env  = None # Environment to be exported in .grip/env
    def __init__(self, git_repo_desc, stage_name, values):
        self.git_repo_desc = git_repo_desc
        self.stage_name = stage_name
        self.wd    = values.wd
        self.env   = values.env
        self.exec  = values.exec
        pass
    def prettyprint(self, acc, pp):
        acc = pp(acc, "%s:" % (self.stage_name))
        if self.wd   is not None: acc = pp(acc, "wd:     %s" % (self.wd), indent=1)
        if self.env  is not None: acc = pp(acc, "env:    %s" % (self.env), indent=1)
        if self.exec is not None: acc = pp(acc, "exec:   %s" % (self.exec), indent=1)
        return acc
    pass

#c GitRepoDesc
class GitRepoDesc(object):
    """
    A GitRepoDesc is a simple object containing the data describing a git repo that is part of a grip repo

    Each GitRepoDesc should have an entry repo.<name> as a table of <property>:<value> in the grip.toml file

    Possibly this can include <install> 

    A GitRepoDesc may have a changeset associated with it from a .grip/state file

    A GitRepoDesc may be read-only; push-to-integration; push-to-patch?; merge?

    Possibly it should have a default dictionary of <stage> -> <GitRepoStageDesc>
    """
    def __init__(self, name, values, parent=None):
        """
        values must be a RepoDescTomlDict._values
        """
        self.name   = name
        self.parent = parent
        self.url    = values.url
        self.branch = values.branch
        self.path   = values.path
        if parent is not None:
            if self.url    is None: self.url = parent.url
            if self.branch is None: self.branch = parent.branch
            if self.path   is None: self.path = parent.path
        self.stages = {}
        for stage in values.Get_other_attrs():
            stage_values = values.Get(stage)
            self.stages[stage] = GitRepoStageDesc(self, stage, stage_values)
        pass
    def prettyprint(self, acc, pp):
        acc = pp(acc, "repo.%s:" % (self.name))
        if self.url    is not None: acc = pp(acc, "url:    %s" % (self.url), indent=1)
        if self.branch is not None: acc = pp(acc, "branch: %s" % (self.branch), indent=1)
        if self.path   is not None: acc = pp(acc, "path:   %s" % (self.path), indent=1)
        for stage_name in self.stages:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent+1)
            acc = self.stages[stage_name].prettyprint(acc,ppr)
            pass
        return acc
    pass

#c GripConfig
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
    repos = {} # dictionary of <repo name> : <GitRepoDesc instance>
    
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.repos = {}
        pass
    def build_from_values(self, values):
        """
        values is a SpecificConfigTomlDict._values

        Hence it has a .repos (possibly None) and other attributes that should be <reponame> of type RepoDescTomlDict._values
        """
        self.repos = {}
        for r in self.parent.base_repos:
            self.repos[r] = self.parent.repos[r]
            pass
        for r in values.repos:
            if r not in self.parent.repos:raise GripTomlError("repo '%s' specified in config '%s' but it is not defined in the file"%(r, self.name))
            self.repos[r] = self.parent.repos[r]
            pass
        for r in values.Get_other_attrs(): # These must be RepoDescTomDict._values
            if r not in self.repos:raise GripTomlError("repo '%s' description specified in config '%s' but it is not one of the repos for that config (repos are %s)"%(r, self.name, self.repos.keys()))
            repo_desc = values.Get(r)
            self.repos[r] = GitRepoDesc(r, repo_desc, parent=self.repos[r])
            pass
        pass
    def prettyprint(self, acc, pp):
        acc = pp(acc, "config.%s:" % (self.name))
        for r in self.repos:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent+1)
            acc = self.repos[r].prettyprint(acc, ppr)
            pass
        return acc
    pass

#c *..TomlDict subclasses to parse toml file contents
class RepoDescTomlDict(TomlDict):
    class RepoStageTomlDict(TomlDict):
        """For e.g. config.standalone.cdl"""
        requires = TomlDictParser.from_dict_attr_list(str) # list of other repos stages completed correctly
        wd       = TomlDictParser.from_dict_attr_value(str)
        env      = TomlDictParser.from_dict_attr_value(str)
        exec     = TomlDictParser.from_dict_attr_value(str)
        pass
    url       = TomlDictParser.from_dict_attr_value(str)
    branch    = TomlDictParser.from_dict_attr_value(str)
    path      = TomlDictParser.from_dict_attr_value(str)
    Wildcard  = TomlDictParser.from_dict_attr_dict(RepoStageTomlDict)
    pass
class GripFileTomlDict(TomlDict):
    class ConfigTomlDict(TomlDict):
        """For config
        All attributes are specific configuration details
        """
        class SpecificConfigTomlDict(TomlDict):
            """For e.g. config.standalone"""
            Wildcard     = TomlDictParser.from_dict_attr_dict(RepoDescTomlDict)
            repos        = TomlDictParser.from_dict_attr_list(str)
            pass
        Wildcard     = TomlDictParser.from_dict_attr_dict(SpecificConfigTomlDict)
        pass
    class RepoTomlDict(TomlDict):
        Wildcard     = TomlDictParser.from_dict_attr_dict(RepoDescTomlDict)
        pass
    configs        = TomlDictParser.from_dict_attr_list(str)
    stages         = TomlDictParser.from_dict_attr_list(str)
    base_repos     = TomlDictParser.from_dict_attr_list(str)
    default_config = TomlDictParser.from_dict_attr_value(str)
    repo           = TomlDictParser.from_dict_attr_dict(RepoTomlDict)
    config         = TomlDictParser.from_dict_attr_dict(ConfigTomlDict)
    pass

#c GripTomlError
class GripTomlError(Exception):
    pass

#c GripRepoDesc
class GripRepoDesc(object):
    """
    A RepoDesc is a complete description of the Grip repo

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
    """
    raw_toml_dict = None
    default_config = None
    base_repos = []
    configs = {}
    repos = {}
    stages = []
    def __init__(self):
        self.default_config = None
        self.repos = {}
        self.configs = {}
        self.stages = []
        self.base_repos = []
        pass
    def read_toml_file(self, grip_toml_filename):
        """
        Load the <root_dir>/.grip/grip.toml file
        """
        self.raw_toml_dict = toml.load(grip_toml_filename)
        values = TomlDictParser.from_dict(GripFileTomlDict, self, "", self.raw_toml_dict)
        # values.Prettyprint()
        self.build_from_values(values)
        pass
    def build_from_values(self, values):
        if values.base_repos is not None: self.base_repos = values.base_repos
        if values.default_config is not None: self.default_config = values.default_config
        if values.repo    is None: raise GripTomlError("'repo' entries must be provided (empty grip configuration is not supported)")
        for repo_name in values.repo.Get_other_attrs():
            self.repos[repo_name] = GitRepoDesc(repo_name, values.repo.Get(repo_name))
            pass
        for r in self.base_repos:
            if r not in self.repos: raise GripTomlError("repo '%s' is in base_repos but has not been described"%r)
            pass
        if values.configs is None: raise GripTomlError("'configs' must be provided")
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
        if self.default_config not in self.configs:raise GripTomlError("default_config of '%s' is undefined (defined configs are %s)" % (self.default_config, self.configs.keys()))
        pass
    def prettyprint(self, acc, pp):
        acc = pp(acc, "default_config: %s"%(self.default_config))
        acc = pp(acc, "base_repos:     %s"%(str(self.base_repos)))
        for r in self.repos:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent)
            acc = self.repos[r].prettyprint(acc, ppr)
            pass
        for c in self.configs:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent)
            acc = self.configs[c].prettyprint(acc, ppr)
            pass
        return acc
    pass

#a Top level
x = GripRepoDesc()
x.read_toml_file("./.grip/grip.toml")
def p(acc,s,indent=0):
    return acc+"\n"+("  "*indent)+s
print(x.prettyprint("",p))
