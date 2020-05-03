#a Imports
import os, sys, re, copy
import toml
from .tomldict import TomlDict, TomlDictParser
from .git import GitRepo
from .workflows import workflows
from .exceptions import *

#a Exceptions
#c GripEnvError - exception used when reading the grip toml file
class GripEnvError(ConfigurationError):
    grip_type = "Grip repository environment error"
    def __init__(self, grip_env, key, reason):
        s = "Environment error in '%s' for '%s': %s"%(grip_env.full_name(), key, reason)
        self.grip_env = grip_env
        self.key =key
        self.reason = reason
        GripException.__init__(self,s)
        pass
    pass
class GripEnvValueError(GripEnvError):
    """
    Exception that may be handled to return "" if environment is not critical
    """
    pass

#c GripTomlError - exception used when reading the grip toml file
class GripTomlError(ConfigurationError):
    pass

#c RepoDescError - exception used when a repo description is invalid
class RepoDescError(ConfigurationError):
    pass

#a Classes
#c EnvTomlDict
class EnvTomlDict(TomlDict):
    Wildcard     = TomlDictParser.from_dict_attr_value(str)
    pass

#c GripEnv
class GripEnv:
    #v regular expressions
    name_match_re = r"""(?P<name>([^@]*))@(?P<rest>.*)$"""
    name_match_re = re.compile(name_match_re)
    #f __init__
    def __init__(self, parent=None, name=None, default_values={}):
        self.name = name
        self.parent = parent
        self.env = {}
        self.add_values(default_values)
        pass
    #f get_root
    def get_root(self):
        if self.parent is not None: return self.parent.get_root()
        return self
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
    def resolve(self, error_handler=None):
        """
        Resolve the values in the environment where the values include references
        to other environment variables (with @KEY@)
        """
        unresolved_env = list(self.env.keys())
        while unresolved_env != []:
            not_done_yet = []
            work_done = False
            while len(unresolved_env)>0:
                k = unresolved_env.pop(0)
                v = self.substitute(self.env[k], finalize=False, error_handler=error_handler)
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
                v = self.substitute(k, self.env[k], finalize=True, error_handler=error_handler)
                GripEnvValueError(self,k,"Circular environment dependency (value '%s')"%(self.env[k])).invoke(error_handler)
                break
            pass
        # Capture the environment keys to resolve - self.env itself may change in our loop if error handlers add values
        env_to_resolve = list(self.env.keys())
        for k in env_to_resolve:
            self.env[k] = self.substitute(self.env[k], finalize=True, error_handler=error_handler)
            pass
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
    def value_of_key(self, k, raise_exception=True, environment_overrides=True, error_handler=None):
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
        return GripEnvValueError(self,k,"Configuration or environment value not specified").invoke(error_handler)
    #f substitute
    def substitute(self, s, acc="", finalize=True, error_handler=None):
        """
        Find any @ENV_VARIABLE@ and replace - check ENV_VARIABLE exists, raise exception if it does not
        Find any @@ and replace

        if not finalizing, then leave @@ as @@, and don't raise exceptions as another pass should do it
        """
        if s is None: return None
        n = s.find("@")
        if n<0: return acc+s
        if len(s)==n+1:
            if not finalize: return None
            raise GripTomlError("Unexpected '@' at end of string using environment %s",self.full_name())
        acc = acc + s[:n]
        m = self.name_match_re.match(s,n+1)
        if m is None:
            if not finalize: return None
            return GripEnvError(self, s, "Could not parse (char %d) as a grip environment substitution"%(n+1)).invoke(error_handler)
        k = m.group('name')
        if len(k)==0:
            v="@"*2
            if finalize: v="@"
            pass
        else:
            v = self.value_of_key(k, raise_exception=finalize, error_handler=error_handler)
            if v is None: return None
            pass
        acc = acc + v
        return self.substitute(m.group('rest'), acc=acc, finalize=finalize, error_handler=error_handler)
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

#a Unittest for GripRepoDesc class
from .test_utils import UnitTestObject
class GripEnvUnitTestBase(UnitTestObject):
    pass
