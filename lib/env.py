#a Imports
import os, sys, re, copy
from typing import Optional, Dict, List, Tuple, cast
from .tomldict import TomlDict, TomlDictValues, TomlDictParser
# Specifically this imports type ErrorHandler (plus all exceptions)
from .exceptions import *
from .verbose import Verbose
from .types import MakefileStrings, EnvDict

#a Exceptions
#c GripEnvError - exception used when reading the grip toml file
class GripEnvError(ConfigurationError):
    grip_type = "Grip repository environment error"
    def __init__(self, grip_env:'GripEnv', key:str, reason:str):
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

#a Classes
#c EnvTomlDict
class EnvTomlDict(TomlDict):
    Wildcard     = TomlDictParser.from_dict_attr_value(str)
    pass

#c GripEnv
class GripEnv:
    #t instance property types
    verbose : Verbose
    parent  : Optional['GripEnv']
    env     : EnvDict
    
    #v regular expressions
    name_match_re_string = r"""(?P<name>([a-zA-Z_][a-zA-Z_0-9]*))@(?P<rest>.*)$"""
    name_match_re = re.compile(name_match_re_string)
    #f __init__
    def __init__(self, parent:Optional['GripEnv']=None, name:str="<unnamed env>", default_values:EnvDict={}, opt_verbose:Optional[Verbose]=None):
        self.name = name
        self.parent = parent
        self.env = {}
        self.add_values(default_values)
        root = self.get_root()
        if opt_verbose is None:
            assert self!=root
            assert parent != None
            self.verbose = root.verbose
            pass
        else:
            self.verbose = opt_verbose
            pass
        pass
    #f set_parent
    def set_parent(self, parent:'GripEnv') -> None:
        """
        Use to insert a lower priority dictionary between this environment and its parent
        """
        self.parent = parent
        pass
    #f get_root - find root environment by tracing parents
    def get_root(self) -> 'GripEnv':
        if self.parent is not None: return self.parent.get_root()
        return self
    #f add_values - add values from a dictionary to the environment
    def add_values(self, values_d:EnvDict) -> None:
        """
        Add values from the dictionary 'values_d' to this environment
        """
        for (k,v) in values_d.items():
            self.env[k] = v
            pass
        pass
    #f build_from_values - build from TomlDictValues 'other attributes'
    def build_from_values(self, values : Optional[TomlDictValues]) -> None:
        """
        Add key/value pairs from a TomlDictValues 'other attributes'
        """
        if values is None: return
        for k in values.Get_other_attrs():
            self.env[k] = values.Get(k)
            pass
        pass
    #f resolve - resolve self.env looking for @KEY@ in each
    def resolve(self, error_handler:ErrorHandler=None) -> None:
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
                # for circular dependencies we will eventually get self.env[k] to contain @k@
                # This will not error though
                v = self.substitute(self.env[k], on_behalf_of=k, finalize=False, error_handler=error_handler)
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
            # Keep the list going ...
            unresolved_env = not_done_yet
            # ... but if no work was done, then we are stuck
            if not work_done:
                k = not_done_yet[0]
                v = self.substitute(self.env[k], on_behalf_of=k, finalize=False, error_handler=error_handler)
                # raise("Circular environment dependency (value '%s')"%(self.env[k]))
                GripEnvValueError(self,k,"Circular environment dependency (value '%s')"%(self.env[k])).invoke(error_handler)
                break
            pass
        # Capture the environment keys to resolve - self.env itself may change in our loop if error handlers add values
        env_to_resolve = list(self.env.keys())
        for k in env_to_resolve:
            e = self.substitute(self.env[k], on_behalf_of=k, finalize=True, error_handler=error_handler)
            if e is not None: self.env[k] = e
            pass
        pass
    #f full_name - get hierarchical name of environment
    def full_name(self) -> str:
        """
        Return a string with the full hierarchial name of this environment
        """
        r = ""
        if self.parent is not None:
            r = self.parent.full_name()+"."
            pass
        return r+self.name
    #f value_of_key - get value of key, from parents if not local, using environment if required
    def value_of_key(self, k : str, ignore_local:bool=False, raise_exception:bool =True, environment_overrides:bool =True, error_handler:ErrorHandler=None) -> Optional[str]:
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
        if not ignore_local:
            if k in self.env: r=self.env[k]
            pass
        if (r is None) and (self.parent is not None):
            r = self.parent.value_of_key(k, ignore_local=False, raise_exception=False, environment_overrides=False)
            pass
        if r is not None: return r
        if not raise_exception: return None
        e = GripEnvValueError(self,k,"Configuration or environment value not specified, or circular dependency").invoke(error_handler)
        assert ((e is None) or (type(e)==str))
        return cast(Optional[str],e)
    #f _substitute - substitute environment contents as required in a string, return None if unknown variable
    def _substitute(self, s:Optional[str], on_behalf_of:Optional[str], acc:str="", finalize:bool=True, error_handler:ErrorHandler=None) -> Optional[str]:
        """
        Find any @ENV_VARIABLE@ and replace - check ENV_VARIABLE exists, raise exception if it does not
        Find any @@ and replace

        if not finalizing, then leave @@ as @@, and don't raise exceptions as another pass should do it
        """
        if s is None: return None
        n = s.find("@")
        if n<0: return acc+s
        acc = acc + s[:n]
        m = self.name_match_re.match(s,n+1)
        if m is None:
            acc = acc + "@"
            return self._substitute(s[n+1:],on_behalf_of=on_behalf_of,acc=acc,finalize=finalize,error_handler=error_handler)
        k = m.group('name')
        if len(k)==0:
            v="@"*2
            if finalize: v="@"
            pass
        else:
            ignore_local = (k==on_behalf_of)
            key_value = self.value_of_key(k, ignore_local=ignore_local, raise_exception=finalize, error_handler=error_handler)
            if key_value is None: return None
            v = key_value
            pass
        acc = acc + v
        return self._substitute(m.group('rest'), on_behalf_of=on_behalf_of, acc=acc, finalize=finalize, error_handler=error_handler)
    #f substitute - substitute environment contents as required in a string, return None if unknown variable
    def substitute(self, s:Optional[str], on_behalf_of:Optional[str]=None, finalize:bool=True, error_handler:ErrorHandler=None) -> Optional[str]:
        """
        Find any @ENV_VARIABLE@ and replace - check ENV_VARIABLE exists, raise exception if it does not
        Find any @@ and replace

        if not finalizing, then leave @@ as @@, and don't raise exceptions as another pass should do it
        """
        try:
            opt_result = self._substitute(s=s, on_behalf_of=on_behalf_of, acc="", finalize=finalize, error_handler=error_handler)
            pass
        except:
            assert finalize
            self.verbose.warning("Envrionment failed to substitute in '%s' for %s"%(str(s), on_behalf_of))
            raise
        return opt_result
    #f as_dict - generate key->value pair, including parent if required
    def as_dict(self, include_parent:bool=False) -> EnvDict:
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
    def as_makefile_strings(self, include_parent:bool=False) -> MakefileStrings:
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
    #f as_str - Generate a string for pretty printing
    def as_str(self, include_parent:bool=False) -> str:
        """
        Generate a string representation of the environment, including parents if required
        Used for pretty-printing
        """
        r = []
        d = self.as_dict(include_parent=include_parent)
        for (k,v) in d.items():
            r.append("%s:'%s'"%(k,v))
            pass
        return " ".join(r)
    #f show - print environment for humans for debug
    def show(self, msg:str, include_parent:bool=False) -> None:
        """
        Print environment for debugging, including the parent environments if desired
        """
        d = self.as_dict(include_parent=include_parent)
        if msg is not None: print("Environment for %s:%s"%(self.full_name(), msg))
        for (k,v) in d.items():
            print("    '%s' : '%s'"%(k,v))
            pass
        pass

