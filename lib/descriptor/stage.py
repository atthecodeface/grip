#a Imports
import os
from typing import Optional, List, Callable, Type, ClassVar, Union, Any
from ..tomldict import TomlDict, TomlDictValues, TomlDictParser
from ..exceptions import *
from ..env import GripEnv, EnvTomlDict

#a Classes
#c StageTomlDict - Toml dictionary that describes a stage
class StageTomlDict(TomlDict):
    """For e.g. config.standalone.cdl"""
    requires  = TomlDictParser.from_dict_attr_list(str) # list of other repos dependencies completed correctly
    satisfies = TomlDictParser.from_dict_attr_value(str) # repo dependency (local or global)
    wd       = TomlDictParser.from_dict_attr_value(str)
    doc      = TomlDictParser.from_dict_attr_value(str)
    env      = TomlDictParser.from_dict_attr_dict(EnvTomlDict)
    exec     = TomlDictParser.from_dict_attr_value(str)
    action   = TomlDictParser.from_dict_attr_bool()
    pass

#c Dependency
class Dependency:
    """
    This class is a stage dependency - that is '<name>', '.<name>' or '<repo>.<name>'
    """
    #v makefile_path_fn - function from Dependency instance to its makefile stamp path - class property
    makefile_path_fn : ClassVar = None
    #v instance properties
    repo_name : str
    stage_name : str
    stage : Type['Descriptor']
    #f set_makefile_path_fn - class method - set makefile_path_fn for the whole class
    @classmethod
    def set_makefile_path_fn(cls, path_fn):
        cls.makefile_path_fn = path_fn
        pass
    #f __init__
    def __init__(self, s, git_repo_desc=None, must_be_global=True, force_local=False):
        repo_name=None
        if git_repo_desc is not None: repo_name=git_repo_desc.name
        s_split = s.split(".")
        s_stage_name = s_split[0]
        s_repo_name = None
        if len(s_split)==1:
            if force_local: s_repo_name = repo_name
            pass
        elif len(s_split)==2:
            s_repo_name  = s_split[0]
            s_stage_name = s_split[1]
            if must_be_global: raise GripTomlError("Bad repo dependency '%s' - must be global, no '.'s"%s)
            if force_local: raise GripTomlError("Bad repo dependency '%s' - must be local, no '.'s"%s)
            pass
        else:
            if force_local: raise GripTomlError("Bad repo dependency '%s' - must be local, no '.'s"%s)
            raise GripTomlError("Bad repo dependency '%s' - must be <global stage>, .<local stage> or <repo>.<repo stage>"%s)
        if s_repo_name=="": s_repo_name = repo_name
        self.repo = None
        self.stage = None
        self.repo_name = s_repo_name
        self.stage_name = s_stage_name
        pass
    #f validate
    def validate(self, grip_config, reason, error_handler=None):
        if self.repo_name is not None:
            self.repo = grip_config.get_repo(self.repo_name, error_on_not_found=False)
            if self.repo is None:
                return GripTomlError("%s: repo not in configuration '%s'"%(reason, grip_config.get_name())).invoke(error_handler)
            self.stage = self.repo.get_repo_stage(self.stage_name, error_on_not_found=False)
            if self.stage is None:
                return GripTomlError("%s: stage '%s' not in repo '%s' in configuration '%s'"%(reason, self.stage_name, self.repo.name, grip_config.get_name())).invoke(error_handler)
            pass
        else:
            if not grip_config.has_stage(self.stage_name):
                return GripTomlError("%s: not a global stage in configuration '%s'"%(self.stage_name, grip_config.get_name())).invoke(error_handler)
            pass
        pass
    #f full_name - return the full name - <stage_name> if global, else <repo_name>.<stage_name>
    def full_name(self) -> str:
        if self.repo_name is None: return self.stage_name
        return "%s.%s"%(self.repo_name, self.stage_name)
    #f target_name - return string for the makefile *target*
    def target_name(self) -> str:
        if self.repo_name is None: return self.stage_name
        return "repo.%s.%s"%(self.repo_name, self.stage_name)
    #f makefile_path - invoke the class property makefile_path_fn on *this* instance to get its makefile stamp path
    def makefile_path(self):
        """
        Return the pathname for a makefile target for an instance of this class
        """
        if self.makefile_path_fn is None:
            raise Exception("Bug - makefile_path_fn not supplied")
        return self.makefile_path_fn(self)
    #f makefile_stamp
    def makefile_stamp(self) -> str:
        """
        Get makefile stamp of a 'stage', 'requires' or 'satisfies'
        """
        return self.target_name()
    #f new_makefile_stamp
    def new_makefile_stamp(self):
        """
        Get an absolute path to a makefile stamp filename
        Clean the file if it exists

        If repo is None then it is a global stage
        """
        tgt      = self.target_name()
        tgt_path = self.makefile_path()
        if os.path.exists(tgt_path): os.unlink(tgt_path)
        return (tgt, tgt_path)
    #f All done
    pass

#c DescriptorValues - namespace that contains values from the TomlDict
class DescriptorValues(object):
    wd   = None # Working directory to execute <exec> in (relative to repo desc path)
    exec = None # Shell script to execute to perform the stage
    env  : Union[TomlDictValues, None] = None # Environment to be exported in .grip/env
    doc = None
    action = False
    requires : List[str]= []
    satisfies = None
    #f clone  = clone to get required values from the other
    @classmethod
    def clone(cls, other):
        c = cls()
        c.wd = other.wd
        c.env = other.env
        c.exec = other.exec
        c.requires = other.requires[:]
        c.satisfies = other.satisfies
        c.doc = other.doc
        c.action = other.action
        return c

#c Descriptor - What to do for a stage of a configuration or a particular grip repo module
class Descriptor(object):
    """
    This has the data for a particular installation or build mechanism and dependencies for a git repo or config

    It a stage name (e.g. install, test, etc) and how to perform the stage

    It may have a git_repo_desc (which it is for); if it is for a config, though, this will be None
    """
    values          : Type['DescriptorValues']
    requires        : List[Dependency]
    satisfies       : List[Dependency]
    grip_repo_desc  : Any # Type['GripRepoDesc']
    #f __init__
    def __init__(self, grip_repo_desc, name, clone=None, git_repo_desc=None, values=None):
        self.grip_repo_desc = grip_repo_desc
        self.git_repo_desc = git_repo_desc # May be None
        self.grip_config = None # Will be set by validate
        self.name = name
        self.dependency = Dependency(name, git_repo_desc=self.git_repo_desc, force_local=True)
        self.cloned_from = clone
        if clone is not None:
            self.values = clone.values.clone(clone.values)
            pass
        else:
            self.values = DescriptorValues()
            pass
        if values is not None:
            values.Set_obj_properties(self.values, values.Get_fixed_attrs())
            pass
        pass
    #f clone - clone the stage descriptor, particularly to instantiate it within a particular config
    def clone(self, grip_repo_desc=None, git_repo_desc=None, values=None):
        if grip_repo_desc is None: grip_repo_desc = self.grip_repo_desc
        if git_repo_desc is None:  git_repo_desc = self.git_repo_desc
        return self.__class__(grip_repo_desc=grip_repo_desc, git_repo_desc=git_repo_desc, name=self.name, clone=self, values=values)
    #f get_name - Get name of the stage
    def get_name(self) -> str:
        return self.name
    #f is_action - Return true if marked as an action (i.e. does not require a makefile stamp)
    def is_action(self):
        return self.values.action
    #f resolve - Resolve the stage environment and resolve relevant entries within that
    def resolve(self, env : GripEnv , error_handler=None) -> None:
        """
        Resolve any environment substitutions using the repo desc's (within configuration) environment - but not in 'requires'
        This includes resolving the local environment
        """
        self.env = GripEnv(name="stage %s"%self.name, parent=env)
        self.env.build_from_values(self.values.env)
        self.env.resolve(error_handler=error_handler)
        self.wd   = env.substitute(self.values.wd,   error_handler=error_handler)
        self.exec = env.substitute(self.values.exec, error_handler=error_handler)
        self.doc = self.values.doc
        pass
    #f validate - Validate the within a particular configuration
    def validate(self, grip_config, check_dependencies=True, error_handler=None):
        self.grip_config = grip_config
        self.requires = []
        for r in self.values.requires:
            self.requires.append(Dependency(r, git_repo_desc=self.git_repo_desc, must_be_global=False))
            pass
        self.satisfies = []
        if self.values.satisfies is not None:
            self.satisfies.append(Dependency(self.values.satisfies, git_repo_desc=self.git_repo_desc, must_be_global=False))
            pass
        repo_name = "<global!!>"
        if self.git_repo_desc is not None:
            repo_name = self.git_repo_desc.name
            pass
        for r in self.requires:
            r.validate(grip_config, reason="Repo stage '%s.%s' requires of '%s'"%(repo_name, self.name, r.full_name()), error_handler=error_handler)
            pass
        for s in self.satisfies:
            s.validate(grip_config, reason="Repo stage '%s.%s' satisfies of '%s'"%(repo_name, self.name, s.full_name()), error_handler=error_handler)
            pass
        pass
    #f get_doc_string
    def get_doc_string(self):
        """
        Get documentation string for this configuration
        """
        if self.doc is None: return None
        return self.doc.strip()
    #f write_makefile_entries
    def write_makefile_entries(self, f, verbose : Callable[[str], None]):
        (tgt, tgt_filename) = self.dependency.new_makefile_stamp()
        sn = self.get_name()
        if self.git_repo_desc is None:
            verbose("Adding global stage '%s'"%sn)
            rs_name = "%s"%(sn)
            pass
        else:
            verbose("Adding target '%s'"%tgt)
            rs_name = "%s_%s"%(self.git_repo_desc.name, sn)
            pass

        wd = self.wd
        if wd is None:
            if self.git_repo_desc is None:
                wd = self.grip_repo_desc.git_repo.filename()
                pass
            else:
                wd = self.grip_repo_desc.git_repo.filename(self.git_repo_desc.path)
                pass
            pass

        env = ""
        for (k,v) in self.env.as_makefile_strings():
            env = env + (" %s=%s"%(k,v))
            pass
        if env != "": env = env + ";"

        print("\nGRIP_%s_ENV := %s"%(rs_name, env), file=f)

        print("\n.PHONY: %s revoke.%s force.%s"%(tgt, tgt, tgt), file=f)
        print("%s: %s"%(tgt, tgt_filename), file=f)
        print("revoke.%s:\n\trm -f %s"%(tgt, tgt_filename), file=f)
        print("force.%s: revoke.%s\n\t${MAKE} -f ${THIS_MAKEFILE} ${MAKEFLAGS} %s"%(tgt, tgt,tgt), file=f)

        print("%s:"%(tgt_filename), file=f)
        print("\t${GQE} 'Executing %s'"%(rs_name), file=f)
        if self.exec is not None:
            print("\t${GQ}${GRIP_%s_ENV} cd %s && (%s)"%(rs_name, wd, self.exec), file=f)
            pass
        if not self.is_action():
            print("\t${GQ}touch %s"%(tgt_filename), file=f)
            pass

        for r in self.requires:
            verbose(".. Dependent on '%s'"%(r.target_name()))
            ostgt_filename = r.makefile_path()
            print("%s: %s"%(tgt_filename,ostgt_filename), file=f)
            pass

        for s in self.satisfies:
            assert self.git_repo_desc is not None
            verbose("Global stage '%s' depends on repo '%s' stage '%s'"%(s.target_name(), self.git_repo_desc.name, self.name))
            ostgt          = s.makefile_stamp()
            ostgt_filename = s.makefile_path()
            print("%s: %s"%(ostgt_filename, tgt_filename), file=f)
            print("revoke.%s: revoke.%s"%(ostgt, tgt), file=f)
            print("force.%s: force.%s"%(ostgt, tgt), file=f)
            pass

        if self.git_repo_desc is not None:
            config_stage = self.grip_config.get_stage(self.name)
            if config_stage is not None:
                verbose("Global stage '%s' depends on repo '%s' of same name"%(config_stage.name, self.git_repo_desc.name))
                stgt_filename = config_stage.dependency.makefile_path()
                print("%s: %s"%(stgt_filename, tgt_filename), file=f)
                pass
            pass
        pass
    #f prettyprint
    def prettyprint(self, acc : str, pp) -> str:
        acc = pp(acc, "%s:" % (self.name))
        if self.wd   is not None: acc = pp(acc, "wd:     %s" % (self.wd), indent=1)
        if self.env  is not None:
            if isinstance(self.env, GripEnv): acc = pp(acc, "env:    %s" % (self.env.as_str()), indent=1)
            else: acc = pp(acc, "env:    %s" % ("<unresolved values>"), indent=1)
        if self.exec is not None: acc = pp(acc, "exec:   %s" % (self.exec), indent=1)
        if self.values.requires != []:acc = pp(acc, "requires:   '%s'" % (" ".join(self.values.requires)), indent=1)
        if self.values.satisfies is not None:acc = pp(acc, "satisfies:   '%s'" % (self.values.satisfies), indent=1)
        return acc
    #f All done
    pass

