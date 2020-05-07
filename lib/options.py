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
    def __init__(self):
        pass
    #f has - return true if we have an option
    def has(self, n) -> bool:
        return hasattr(self,n)
    # get - get an option with a default, or raise exception
    def get(self, n:str, default=UnknownOption) -> Any:
        if self.has(n): return getattr(self,n)
        if default is UnknownOption: raise UnknownOption("Option %s unknown"%n)
        return default
    #f _validate - validate the options
    def _validate(self):
        if (type(self.verbose)==bool) or (type(self.quiet)==bool):
            verbose = Verbose(level=Verbose.level_info)
            if (type(self.verbose)==bool) and self.verbose: verbose.set_level(Verbose.level_verbose)
            elif (type(self.quiet)==bool) and self.quiet:   verbose.set_level(Verbose.level_warning)
            else:              verbose.set_level(Verbose.level_info)
            self.verbose = verbose
            pass
        elif type(self.verbose)==int:
            self.verbose = Verbose(level=self.verbose)
            pass
        pass
    #f dump - print to screen
    def dump(self):
        for k in dir(self):
            print(k,self.get(k))
            pass
        pass
    pass

