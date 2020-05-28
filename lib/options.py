#a Imports
from typing import Type, Dict, List, Sequence, Any
from .exceptions import *
from .verbose import Verbose

#c Options
class UnknownOption(Exception):pass
class Options(object):
    """
    The argparse options must be a namespace, that is all

    Hence this class is used for 'options'
    """
    verbose  = False
    help     = False
    show_log = False
    quiet    = False
    _verbose_fn : Verbose
    #f __init__
    def __init__(self) -> None:
        pass
    #f has - return true if we have an option
    def has(self, n:str) -> bool:
        return hasattr(self,n)
    #f get - get an option with a default, or raise exception
    def get(self, n:str, default:Any=UnknownOption) -> Any:
        if self.has(n): return getattr(self,n)
        if default is UnknownOption: raise UnknownOption("Option %s unknown"%n)
        return default
    #f _validate - validate the options
    def _validate(self) -> None:
        self._verbose_fn = Verbose(level=Verbose.level_info)
        if (type(self.verbose)==bool) or (type(self.quiet)==bool):
            if (type(self.quiet)==bool) and self.quiet:
                self._verbose_fn.set_level(Verbose.level_warning)
                pass
            if (type(self.verbose)==bool) and self.verbose:
                self._verbose_fn.set_level(Verbose.level_verbose)
                pass
            pass
        elif type(self.verbose)==int:
            self._verbose_fn.set_level(self.verbose)
            pass
        pass
    #f get_verbose_fn
    def get_verbose_fn(self) -> Verbose:
        return self._verbose_fn
    #f dump - print to screen
    def dump(self) -> None:
        print("*"*80)
        for k in dir(self):
            if k[0]=='_': continue
            print(k,self.get(k))
            pass
        pass
    pass

