#a Imports
import os, sys, re, copy
import toml
from .tomldict import TomlDict, TomlDictParser
from .git import GitRepo
from .workflows import workflows

#a Useful functions
def str_keys(d):
    return ", ".join([k for k in d.keys()])
              
#a Toml parser classes - description of a .grip/grip.toml file
#c *..TomlDict subclasses to parse toml file contents
class EnvTomlDict(TomlDict):
    Wildcard     = TomlDictParser.from_dict_attr_value(str)
    pass
class RepoDescTomlDict(TomlDict):
    """A repo description: where it is, which VCS it uses, pull methodology, push methodology, where it exists,
    and what to do with it for various grip stages
    """
    class RepoStageTomlDict(TomlDict):
        """For e.g. config.standalone.cdl"""
        requires = TomlDictParser.from_dict_attr_list(str) # list of other repos stages completed correctly
        wd       = TomlDictParser.from_dict_attr_value(str)
        env      = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
        exec     = TomlDictParser.from_dict_attr_value(str)
        pass
    url       = TomlDictParser.from_dict_attr_value(str)
    workflow  = TomlDictParser.from_dict_attr_value(str)
    branch    = TomlDictParser.from_dict_attr_value(str)
    path      = TomlDictParser.from_dict_attr_value(str)
    shallow   = TomlDictParser.from_dict_attr_value(str)
    env       = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
    doc       = TomlDictParser.from_dict_attr_value(str)
    Wildcard  = TomlDictParser.from_dict_attr_dict(RepoStageTomlDict)
    pass
class GripFileTomlDict(TomlDict):
    class ConfigTomlDict(TomlDict):
        """Dictionary of config name -> configuration repos and repo descriptions
        """
        class SpecificConfigTomlDict(TomlDict):
            """Configuration description: repos, and repo descriptions
            """
            Wildcard     = TomlDictParser.from_dict_attr_dict(RepoDescTomlDict)
            repos        = TomlDictParser.from_dict_attr_list(str)
            env          = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
            doc          = TomlDictParser.from_dict_attr_value(str)
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
    workflow       = TomlDictParser.from_dict_attr_value(str)
    name           = TomlDictParser.from_dict_attr_value(str)
    env            = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
    doc            = TomlDictParser.from_dict_attr_value(str)
    pass

#a Classes
#c GripEnv
class GripEnv:
    #v regular expressions
    name_match_re = r"""(?P<name>([^%]*))%(?P<rest>.*)$"""
    name_match_re = re.compile(name_match_re)
    #f __init__
    def __init__(self, parent=None, name=None, default_values={}):
        self.name = name
        self.parent = parent
        self.env = {}
        self.add_values(default_values)
        pass
    #f add_values
    def add_values(self, values_d):
        """
        Add values from the dictionary 'values_d' to this environment
        """
        for (k,v) in values_d.items():
            self.env[k] = v
            pass
        pass
    #f build_from_values
    def build_from_values(self, values):
        """
        Add key/value pairs from a TomlDict.values 'other attributes'
        """
        if values is None: return
        for k in values.Get_other_attrs():
             self.env[k] = values.Get(k)
             pass
        pass
    #f resolve
    def resolve(self):
        """
        Resolve the values in the environment where the values include references
        to other environment variables (with %KEY%)
        """
        unresolved_env = list(self.env.keys())
        while unresolved_env != []:
            not_done_yet = []
            work_done = False
            while len(unresolved_env)>0:
                k = unresolved_env.pop(0)
                v = self.substitute(self.env[k], finalize=False)
                # print("env.substitute %s %s %s %s"%(self.full_name(),k,self.env[k],v))
                if v is None:
                    not_done_yet.append(k)
                    pass
                elif v==self.env[k]:
                    work_done = True
                    pass
                else: # Updated, but it may need a further spin
                    self.env[k] = v
                    not_done_yet.append(k)
                    work_done = True
                    pass
                pass
            if not work_done:
                k = not_done_yet[0]
                v = self.substitute(k, self.env[k], finalize=True)
                raise Exception("Failed to resolve environment '%s' key %s value '%s'"%(self.full_name(),k,self.env[k]))
            pass
        for k in self.env:
            self.env[k] = self.substitute(self.env[k], finalize=True)
        pass
    #f full_name
    def full_name(self):
        """
        Return a string with the full hierarchial name of this environment
        """
        r = ""
        if self.parent is not None:
            r = self.parent.full_name()+"."
            pass
        return r+self.name
    #f value_of_key
    def value_of_key(self, k, raise_exception=True, environment_overrides=True):
        """
        Find value of a key within the environment
        If environment_overrides is True then first look in os.environ
        Look in local environment
        Return None if not found and raise_exception is False
        Raise exception if not found and raise_exception is True
        """
        if environment_overrides and (k in os.environ):
            return os.environ[k]
        r = None
        if k in self.env: r=self.env[k]
        if (r is None) and (self.parent is not None):
            r = self.parent.value_of_key(k, raise_exception=False, environment_overrides=environment_overrides)
            pass
        if r is not None: return r
        if not raise_exception: return None
        raise Exception("Configuration or environment value '%s' is not specified for %s"%(k,self.full_name()))
    #f substitute
    def substitute(self, s, acc="", finalize=True):
        """
        Find any %ENV_VARIABLE% and replace - check ENV_VARIABLE exists, raise exception if it does not
        Find any %% and replace

        if not finalizing, then leave %% as %%, and don't raise exceptions as another pass should do it
        """
        if s is None: return None
        n = s.find("%")
        if n<0: return acc+s
        if len(s)==n+1:
            if not finalize: return None
            raise Exception("Unexpected '%' at end of string using environment %s",self.full_name())
        acc = acc + s[:n]
        m = self.name_match_re.match(s,n+1)
        if m is None:
            if not finalize: return None
            raise Exception("Could not parse '%s' (%d) as a grip environment substitution (%%....%%) using environment %s"%(s, n+1,self.full_name()))
        k = m.group('name')
        if len(k)==0:
            v="%%"
            if finalize: v="%"
            pass
        else:
            v = self.value_of_key(k, raise_exception=finalize)
            if v is None: return None
            pass
        acc = acc + v
        return self.substitute(m.group('rest'), acc=acc, finalize=finalize)
    #f as_dict
    def as_dict(self, include_parent=False):
        """
        Generate a dictionary of environment
        Include parents if required, with children overriding parents if keys
        are provided in both
        """
        e = {}
        if include_parent and (self.parent is not None):
            e = self.parent.as_dict()
            pass
        for (k,v) in self.env.items():
            e[k]=v
            pass
        return e
    #f as_makefile_strings
    def as_makefile_strings(self, include_parent=False):
        """
        Generate a list of (key,value) pairs from the complete environment
        Include parents (recursively) if desired
        """
        r = []
        d = self.as_dict(include_parent=include_parent)
        for (k,v) in d.items():
            r.append((k,v))
            pass
        return r
    #f as_str
    def as_str(self, include_parent=False):
        """
        Generate a string representation of the environment, including parents if required
        Used for pretty-printing
        """
        d = self.as_dict(include_parent=include_parent)
        for (k,v) in d.items():
            r.append("%s:'%s'"%(k,v))
            pass
        return " ".join(r)
    #f show - print environment for humans for debug
    def show(self, msg, include_parent=False):
        """
        Print environment for debugging, including the parent environments if desired
        """
        d = self.as_dict(include_parent=include_parent)
        if msg is not None: print("Environment for %s:%s"%(self.full_name(), msg))
        for (k,v) in d.items():
            print("    '%s' : '%s'"%(k,v))
            pass
        pass
    
#c GitRepoStageDesc - What to do for a stage of a particular grip repo module
class GitRepoStageDesc(object):
    """
    A GitRepoStageDesc has the data for a particular installation or build mechanism and dependencies for a git repo

    It has a git_repo_desc (which it is for), a stage name (e.g. install, test, etc), and how to perform the stage
    """
    # stage = None # Install/test_install/precommit/?
    # git_repo_desc = None # Git repo descr this is the <stage> of
    wd   = None # Working directory to execute <exec> in (relative to repo desc path)
    exec = None # Shell script to execute to perform the stage
    env  = None # Environment to be exported in .grip/env
    requires = None
    #f __init__
    def __init__(self, git_repo_desc, name, values=None):
        self.git_repo_desc = git_repo_desc
        self.grip_repo_desc = git_repo_desc.grip_repo_desc
        self.name = name
        if values is not None:
            values.Set_obj_properties(self, values.Get_fixed_attrs())
            pass
        pass
    #f clone
    def clone(self):
        c = self.__class__(git_repo_desc=self.git_repo_desc,
                           name=self.name,
                           values=None)
        c.wd = self.wd
        c.env = self.env
        c.exec = self.exec
        c.requires = self.requires
        return c
    #f resolve
    def resolve(self, env):
        """
        Resolve any environment substitutions using the repo desc's (within configuration) environment - but not in 'requires'
        This includes resolving the local environment
        """
        env = GripEnv(name="stage %s"%self.name,
                      parent=env)
        env.build_from_values(self.env)
        self.env = env
        self.env.resolve()
        self.wd   = env.substitute(self.wd)
        self.exec = env.substitute(self.exec)
        pass
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "%s:" % (self.name))
        if self.wd   is not None: acc = pp(acc, "wd:     %s" % (self.wd), indent=1)
        if self.env  is not None:
            if isinstance(self.env, GripEnv): acc = pp(acc, "env:    %s" % (self.env.as_str()), indent=1)
            else: acc = pp(acc, "env:    %s" % ("<unresolved values>"), indent=1)
        if self.exec is not None: acc = pp(acc, "exec:   %s" % (self.exec), indent=1)
        if self.requires is not None:acc = pp(acc, "requires:   '%s'" % (" ".join(self.requires)), indent=1)
        return acc
    #f All done
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
                self.stages[stage] = GitRepoStageDesc(self, stage, stage_values)
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
    #f resolve_git_url
    def resolve_git_url(self, grip_git_url):
        """
        Resolve relative (and those using environment variables?) git urls
        """
        if self.git_url.is_leaf():
            self.git_url.make_relative_to(grip_git_url)
            pass
        pass
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
        if self.doc is None: return "Undocumented"
        return self.doc
    #f add_stages_to_set
    def add_stages_to_set(self, s):
        for k in self.stages:
            s.add(k)
            pass
        pass
    #f get_repo_stages
    def get_repo_stages(self, callback_fn):
        for (sn,s) in self.stages.items():
            callback_fn(self, s)
            pass
        pass
    #f is_shallow
    def is_shallow(self):
        if self.shallow is not None:
            if self.shallow=="yes" or self.shallow=="true":
                return True
            pass
        return False
    #f validate
    def validate(self):
        self.workflow = self.grip_repo_desc.validate_workflow(self.workflow, self.name)
        for sn in self.stages:
            if sn not in self.grip_repo_desc.stages:
                raise GripTomlError("Repo '%s' has stage '%s' which is not part of the grip stages list ('%s')"%(self.name,
                                                                                                                 sn,
                                                                                                                 " ".join(self.grip_repo_desc.stages)))
            pass
        pass
    #f resolve
    def resolve(self, env):
        """
        Resolve the strings in the repo description and its stages, using the repo configuration's environment
        """
        env = GripEnv(name="repo %s"%self.name,
                      parent=env)
        env.build_from_values(self.env)
        self.env = env
        self.url    = self.env.substitute(self.url)
        self.path   = self.env.substitute(self.path)        
        self.branch = self.env.substitute(self.branch)
        try:
            self.git_url = GitRepo.parse_git_url(self.url)
            pass
        except:
            raise GripTomlError("for repo '%s' could not parse git url '%s'"%(self.name, self.url))
        if self.path is None:
            self.path = self.git_url.repo_name
            pass
        self.env.add_values({"GRIP_REPO_PATH":"%GRIP_ROOT_PATH%/"+self.path})
        self.env.resolve()
        for (n,s) in self.stages.items():
            s.resolve(self.env)
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

#c GripConfig - a set of GripRepoDesc's for a configuration of the grip repo
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
    #f __init__
    def __init__(self, name, grip_repo_desc):
        self.name = name
        self.doc = None
        self.grip_repo_desc = grip_repo_desc
        self.env = GripEnv(name="config '%s'"%self.name,
                           parent=grip_repo_desc.env )
        self.repos = {}
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
        for r in values.repos:
            if r not in self.grip_repo_desc.repos:raise GripTomlError("repo '%s' specified in config '%s' but it is not defined in the file"%(r, self.name))
            self.repos[r] = self.grip_repo_desc.repos[r].clone()
            pass
        for r in values.Get_other_attrs(): # These must be RepoDescTomDict._values
            if r not in self.repos:raise GripTomlError("repo '%s' description specified in config '%s' but it is not one of the repos for that config (repos are %s)"%(r, self.name, str_keys(self.repos)))
            repo_desc = values.Get(r)
            self.repos[r] = GitRepoDesc(r, values=repo_desc, parent=self.repos[r], grip_repo_desc=self.grip_repo_desc)
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
    def get_repo(self, repo_name):
        if repo_name not in self.repos: raise Exception("Repository '%s' not know in grip configuration '%s'"%(repo_name, self.name))
        return self.repos[repo_name]
    #f iter_repos
    def iter_repos(self):
        for n in self.repos:
            yield self.repos[n]
            pass
        pass
    #f validate
    def validate(self):
        for r in self.iter_repos():
            r.validate()
            pass
        pass
    #f resolve
    def resolve(self):
        """
        Run through repo descriptions and replace grip environment as required
        """
        self.env.resolve()
        for r in self.iter_repos():
            r.resolve(self.env)
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
        if self.doc is None: return "Undocumented"
        return self.doc.strip()
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
    #f get_stages
    def get_stages(self):
        stages = set()
        for r in self.iter_repos():
            r.add_stages_to_set(stages)
            pass
        return list(stages)
    #f get_repo_stages
    def get_repo_stages(self, callback_fn):
        for r in self.iter_repos():
            r.get_repo_stages(callback_fn)
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
        return acc
    #f __str__
    def __str__(self):
        def pp(acc,s,indent=0): return acc + ("  "*indent) + s + "\n"
        return self.prettyprint("", pp)
    #f All done
    pass

#c GripTomlError - exception used when reading the grip toml file
class GripTomlError(Exception):
    pass

#c RepoDescError - exception used when a repo description is invalid
class RepoDescError(Exception):
    pass

#c GripRepoDesc - complete description of a grip repo, from the grip toml file
class GripRepoDesc(object):
    """
    A GripRepoDesc is a complete description of the Grip repo

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
    workflow   : workflow to use for all repositories unless they override it
    name       : name of repo - used in branchnames
    doc        : documentation
    """
    raw_toml_dict = None
    default_config = None
    base_repos = []
    configs = {}
    repos = {}
    stages = []
    supported_workflows = workflows()
    #f __init__
    def __init__(self, git_repo):
        self.name = None
        self.workflow = None
        self.default_config = None
        self.repos = {}
        self.configs = {}
        self.stages = []
        self.base_repos = []
        self.doc = None
        default_env = {}
        default_env["GRIP_ROOT_URL"]  = git_repo.get_git_url_string()
        default_env["GRIP_ROOT_PATH"] = git_repo.get_path()
        self.env = GripEnv(name='grip.toml', default_values=default_env)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename):
        """
        Load the <root_dir>/.grip/grip.toml file
        """
        self.raw_toml_dict = toml.load(grip_toml_filename)
        values = TomlDictParser.from_dict(GripFileTomlDict, self, "", self.raw_toml_dict)
        self.build_from_values(values)
        self.validate()
        self.resolve()
        pass
    #f read_toml_string
    def read_toml_string(self, grip_toml_string):
        """
        Really used in test only, read description from string
        """
        self.raw_toml_dict = toml.loads(grip_toml_string)
        values = TomlDictParser.from_dict(GripFileTomlDict, self, "", self.raw_toml_dict)
        self.build_from_values(values)
        self.validate()
        self.resolve()
        pass
    #f validate
    def validate(self):
        if self.name is None:
            raise RepoDescError("Unnamed repo descriptors are not permitted - the .grip/grip.toml file should have a toplevel 'name' field")
        self.env.resolve()
        if self.default_config not in self.configs:
            raise RepoDescError("default_config of '%s' is undefined (defined configs are %s)" % (self.default_config, str_keys(self.configs)))
        if self.workflow is not None:
            self.workflow = self.validate_workflow(self.workflow, "grip repo description")
            pass
        for (n,c) in self.configs.items():
            c.validate()
            pass
        pass
    #f resolve
    def resolve(self):
        """
        Resolve any values using grip environment variables to config or default values
        """
        for (n,c) in self.configs.items():
            c.resolve()
            pass
        pass
    #f validate_workflow
    def validate_workflow(self, workflow, user):
        if workflow is None:
            raise RepoDescError("'%s' is does not have a workflow specified"%(user))
        if workflow not in self.supported_workflows:
            raise RepoDescError("workflow '%s' used in %s is not in workflows supported by this version of grip (which are %s)"%(self.workflow, user, str_keys(self.supported_workflows)))
        return self.supported_workflows[workflow]
    #f build_from_values
    def build_from_values(self, values):
        values.Set_obj_properties(self, {"name", "workflow", "base_repos", "default_config", "stages", "doc"})
        if values.repo           is None: raise GripTomlError("'repo' entries must be provided (empty grip configuration is not supported)")
        if values.configs        is None: raise GripTomlError("'configs' must be provided in grip configuration file")
        self.env.build_from_values(values.env)
        for repo_name in values.repo.Get_other_attrs():
            self.repos[repo_name] = GitRepoDesc(repo_name, values=values.repo.Get(repo_name), grip_repo_desc=self)
            pass
        # Must validate the base_repos here so users can assume self.repos[x] is valid for x in self.base_repos
        for r in self.base_repos:
            if r not in self.repos: raise RepoDescError("repo '%s', one of the base_repos, is not one of the repos described (which are %s)"%(r, str_keys(self.repos)))
            pass
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
        pass
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
    #f get_configs
    def get_configs(self):
        return self.configs.keys()
    #f get_doc_string
    def get_doc_string(self):
        """
        Return documentation string
        """
        if self.doc is None: return "Undocumented"
        return self.doc.strip()
    #f get_doc
    def get_doc(self, include_configs=True):
        """
        Return list of (name, documentation) strings
        List should include all configurations
        List should always start with (None, repo.doc) if there is repo doc
        """
        r = []
        r.append((None, self.get_doc_string()))
        if include_configs:
            for (n,c) in self.configs.items():
                r.append(("Configuration %s"%n,c.get_doc_string()))
                pass
            pass
        return r
    #f select_config
    def select_config(self, config_name=None):
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

#a Unittest for GripRepoDesc class
from .test_utils import UnitTestObject
class GripRepoDescUnitTestBase(UnitTestObject):
    config_toml = None
    config_name = False
    grd_assert = None
    cfg_assert = None
    exception_expected = None
    def test_it(self):
        def git_repo():pass
        git_repo.get_git_url_string = lambda:""
        git_repo.get_path = lambda:""
        if self.config_toml is not None:
            grd = GripRepoDesc(git_repo=git_repo)
            if self.exception_expected is not None:
                self.assertRaises(self.exception_expected, grd.read_toml_string, self.config_toml)
                pass
            else:
                grd.read_toml_string(self.config_toml)
                pass
            if self.grd_assert is not None:
                self._test_obj_asserts(grd, self.grd_assert, "grip_repo_desc")
                pass
            if self.config_name is not False:
                cfg = grd.select_config(config_name=self.config_name)
                if cfg is None:
                    self.assertEqual(cfg, self.cfg_assert)
                    pass
                else:
                    self._test_obj_asserts(cfg, self.cfg_assert, "config_desc")
                    pass
                pass
            pass
        pass
    pass
class GripRepoDescUnitTest1(GripRepoDescUnitTestBase):
    """
    Note that only configuration's repodescs have resolved git_url properties
    """
    config_toml = """name="y"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=[]\nrepo={}\n"""
    grd_assert = {"name":"y","default_config":"x", "base_repos":[]}
    pass
class GripRepoDescUnitTestBadDefaultConfig(GripRepoDescUnitTestBase):
    exception_expected = RepoDescError
    config_toml = """name="y"\ndefault_config="ax"\nconfigs=["x"]\nbase_repos=[]\nrepo={}\n"""
    pass
class GripRepoDescUnitTest2(GripRepoDescUnitTestBase):
    config_toml = """name="y"\nworkflow="readonly"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=["fred"]\nrepo.fred={url='a',path='b'}\n"""
    grd_assert = {"base_repos":["fred"],
                  "repos":{
                      "fred":{"name":"fred","url":"a","path":"b"},
                  }
    }
    pass
class GripRepoDescUnitTest3(GripRepoDescUnitTestBase):
    config_toml = """name="y"\nworkflow="readonly"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=[]\nrepo.fred={url='a',path='b'}\n"""
    grd_assert = {"base_repos":[],
                  "repos":{
                      "fred":{"name":"fred","url":"a","path":"b"},
                  }
    }
    pass
class GripRepoDescUnitTest4(GripRepoDescUnitTestBase):
    config_toml = """name="y"\nworkflow="readonly"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=[]\nrepo.fred={url='a',path='b'}\n"""
    grd_assert = {"base_repos":[],
                  "repos":{
                      "fred":{"name":"fred","url":"a","path":"b"},
                  }
    }
    pass
class GripRepoDescUnitTestBadBaseRepos(GripRepoDescUnitTestBase):
    exception_expected = RepoDescError
    config_toml = """name="y"\ndefault_config="x"\nconfigs=["x"]\nbase_repos=["f"]\nrepo.fred={url='a',path='b'}\n"""
    pass
class GripRepoDescUnitTestConfigBase(GripRepoDescUnitTestBase):
    config_toml = """
    name="y"
    workflow="readonly"
    default_config="x"
    configs=["x","y"]
    base_repos=["fred"]
    repo.fred={url='ssh://me@there/path/to/thing.git'}
    repo.jim={url='some/path/to/jim.git',workflow="single"}
    repo.joe={url='git://sourceware.org/git/binutils-gdb.git',workflow="readonly",path="binutils"}
    config.x.repos = ["jim"]
    config.y.fred.path = "nothing"
    config.y.repos = ["joe"]
    """
    pass
class GripRepoDescUnitTestConfig1(GripRepoDescUnitTestConfigBase):
    config_name = "unknown_config"
    cfg_assert = None
    pass
class GripRepoDescUnitTestConfig2(GripRepoDescUnitTestConfigBase):
    config_name = None # default
    cfg_assert = {"name":"x"}
    pass
class GripRepoDescUnitTestConfig3(GripRepoDescUnitTestConfigBase):
    config_name = "x"
    cfg_assert = {"name":"x", "repos":{"fred":{"git_url":{"protocol":"ssh", "user":"me", "host":"there", "path":"path/to/thing.git"}, "path":"thing"}}}
    pass
class GripRepoDescUnitTestConfig4(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"name":"y", "repos":{"fred":{"path":"nothing"}}}
    pass
class GripRepoDescUnitTestConfig5(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"fred":{"workflow":{"name":"readonly"}}}}
    pass
class GripRepoDescUnitTestConfig6(GripRepoDescUnitTestConfigBase):
    config_name = "x"
    cfg_assert = {"repos":{"jim":{"workflow":{"name":"single"}}}}
    pass
class GripRepoDescUnitTestConfig7(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"joe":{"workflow":{"name":"readonly"}}}}
    pass
class GripRepoDescUnitTestConfig8(GripRepoDescUnitTestConfigBase):
    config_name = "y"
    cfg_assert = {"repos":{"joe":{"git_url":{"protocol":"git","host":"sourceware.org", "path":"git/binutils-gdb.git"}, "path":"binutils"}}}
    pass


