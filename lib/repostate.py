#a Imports
import toml
from .tomldict import TomlDict, TomlDictParser

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

#a Classes
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
    #f __init__
    def __init__(self, git_repo_desc, stage_name, values):
        self.git_repo_desc = git_repo_desc
        self.stage_name = stage_name
        self.wd    = values.wd
        self.env   = values.env
        self.exec  = values.exec
        pass
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "%s:" % (self.stage_name))
        if self.wd   is not None: acc = pp(acc, "wd:     %s" % (self.wd), indent=1)
        if self.env  is not None: acc = pp(acc, "env:    %s" % (self.env), indent=1)
        if self.exec is not None: acc = pp(acc, "exec:   %s" % (self.exec), indent=1)
        return acc
    #f All done
    pass

#c GitRepoState - state for a repo in a particular config
class GitRepoState(object):
    """
    A git repository inside a grip repo must point to a particular changeset
    This changeset would normally be on the same branch as the grip repo specifies,
    but for some workflows
    """
    changeset = None
    branch = None
    depth = None
    #f __init__
    def __init__(self, name, repo_desc_config=None, values=None):
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
            if self.branch is None: self.branch = r.branch
            pass
        pass
    #f update_state
    def update_state(self, changeset=None):
        if changeset is not None: self.changeset = changeset
        pass
    #f toml_dict
    def toml_dict(self):
        toml_dict = {"changeset":self.changeset}
        if self.branch is not None: toml_dict["branch"] = self.branch
        if self.depth  is not None: toml_dict["depth"] = self.depth
        return toml_dict
    #f prettyprint
    def prettyprint(self, acc, pp):
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
    repos = {} # dictionary of <repo name> : <GitRepoState instance>
    #f __init__
    def __init__(self, name, values=None):
        self.name = name
        self.repos = {}
        if values is not None:
            self.build_from_values(values)
            pass
        pass
    #f build_from_values
    def build_from_values(self, values):
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
    def toml_dict(self):
        toml_dict = {}
        for (n,r) in self.repos.items():
            toml_dict[n] = r.toml_dict()
            pass
        return toml_dict
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "config.%s:" % (self.name))
        for r in self.repos:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent+1)
            acc = self.repos[r].prettyprint(acc, ppr)
            pass
        return acc
    #f get_repo_state
    def get_repo_state(self, repo_desc_config, repo_name, create_if_new=True):
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
    def update_repo_state(self, repo_name, **kwargs):
        """
        Update state of a repo from its name
        """
        if repo_name not in self.repos: raise Exception("Bug - updating repo state for %s.%s which does not exist"%(self.name,repo_name))
        return self.repos[repo_name].update_state(**kwargs)
    #f All done
    pass

#c GripTomlError - exception used when reading the grip toml file
class GripTomlError(Exception):
    pass

#c GripRepoState - complete description of a grip repo, from the grip toml file
class GripRepoState(object):
    """
    """
    raw_toml_dict = None
    configs = {}
    #f __init__
    def __init__(self):
        self.configs = {}
        pass
    #f read_toml_dict
    def read_toml_dict(self, toml_dict):
        self.raw_toml_dict = toml_dict
        values = TomlDictParser.from_dict(GripStateTomlDict, self, "", self.raw_toml_dict)
        self.build_from_values(values)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename):
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
    def read_toml_string(self, grip_toml_string):
        """
        Really used in test only, read description from string
        """
        return self.read_toml_dict(toml.loads(grip_toml_string))
    #f write_toml_file
    def write_toml_file(self, grip_toml_filename):
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
    def build_from_values(self, values):
        self.configs = {}
        for config_name in values.Get_other_attrs():
            self.configs[config_name] = GripConfig(config_name, values=values.Get(config_name))
            pass
        pass
    #f toml_dict
    def toml_dict(self):
        toml_dict = {}
        for (n,c) in self.configs.items():
            toml_dict[n] = c.toml_dict()
            pass
        return toml_dict
    #f prettyprint
    def prettyprint(self, acc, pp):
        for c in self.configs:
            def ppr(acc, s, indent=0):
                return pp(acc, s, indent=indent)
            acc = self.configs[c].prettyprint(acc, ppr)
            pass
        return acc
    #f select_config
    def select_config(self, config_name=None, create_if_new=True):
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

#a Unittest for GripRepoState class
from .test_utils import UnitTestObject
class GripRepoStateUnitTestBase(UnitTestObject):
    state_toml = None
    config_name = False
    grs_assert = None
    cfg_assert = None
    exception_expected = None
    def test_it(self):
        if self.state_toml is not None:
            grs = GripRepoState()
            if self.exception_expected is not None:
                self.assertRaises(self.exception_expected, grs.read_toml_string, self.state_toml)
                pass
            else:
                grs.read_toml_string(self.state_toml)
                pass
            if self.grs_assert is not None:
                self._test_obj_asserts(grs, self.grs_assert, "grip_repo_state")
                pass
            if self.config_name is not False:
                cfg = grs.select_config(config_name=self.config_name)
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
class GripRepoStateUnitTest1(GripRepoStateUnitTestBase):
    state_toml = """cfga.repo1.changeset="1"\n"""
    grs_assert = {"configs":{"cfga":{"repos":{"repo1":{"changeset":"1"}}}}}
    pass
class GripRepoStateUnitTest2(GripRepoStateUnitTestBase):
    state_toml = """cfga.repo1.changeset="1"\ncfga.repo2.changeset="3"\n"""
    grs_assert = {"configs":{"cfga":{"repos":{"repo2":{"changeset":"3"}}}}}
    pass
class GripRepoStateUnitTestComplex(GripRepoStateUnitTestBase):
    state_toml = """
    cfga.repo1.changeset="1"
    cfga.repo2.changeset="3"
    cfgb.repo3.changeset="apple"
    cfgb.repo1.changeset="banana"
    [cfgc]
    repo1 = {changeset="4"}
    repo2 = {changeset="7"}
    """
    pass
class GripRepoStateUnitTest10(GripRepoStateUnitTestComplex):
    grs_assert = {"configs":{"cfga":{"repos":{
        "repo1":{"changeset":"1"},
        "repo2":{"changeset":"3"},
    }}}}
    pass
class GripRepoStateUnitTest11(GripRepoStateUnitTestComplex):
    grs_assert = {"configs":{"cfgb":{"repos":{
        "repo1":{"changeset":"banana"},
        "repo3":{"changeset":"apple"},
    }}}}
    pass
class GripRepoStateUnitTest12(GripRepoStateUnitTestComplex):
    grs_assert = {"configs":{"cfgc":{"repos":{
        "repo1":{"changeset":"4"},
        "repo2":{"changeset":"7"},
    }}}}
    pass
