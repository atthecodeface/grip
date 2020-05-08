#a Imports
import sys
from typing import Optional, List, Callable, Tuple, Iterable, Any, TypeVar, IO

#a Classes
#c Class log
class Log:
    T = Callable[..., Any]
    Entry = Tuple[T, Any]
    Writer = Callable[[str], Any]
    entries : List[Entry]
    tidy_fn : Optional[T]
    #f __init__
    def __init__(self) -> None:
        self.entries = []
        self.tidy_fn = None
        pass
    #f reset
    def reset(self) -> None:
        self.entries = []
        pass
    #f add_entry
    def add_entry(self, log_fn:T, **kwargs:Any) -> None:
        self.entries.append((log_fn,kwargs))
        pass
    #f set_tidy
    def set_tidy(self, tidy_fn:T) -> None:
        """
        Set the 'tidy' function to be called when user tidies logs up

        This may write, for example, write a log to a logfile
        """
        self.tidy_fn = tidy_fn
        pass
    #f tidy
    def tidy(self, reset:bool=True) -> None:
        if self.tidy_fn: self.tidy_fn()
        if reset: self.reset()
        pass
    #f iter - iterate over entries
    def iter(self) -> Iterable[Entry]:
        for e in self.entries:
            yield(e)
            pass
        pass
    #f add_entry
    def add_entry_string(self, s:str) -> None:
        self.add_entry(self.write_string,s=s)
        pass
    #f write_entry
    def write_entry(self, e:Entry, writer:Optional[Writer]=None) -> Any:
        (log_fn, kw_args)=e
        r : List[str] = [] # Actually list of anything, but pick a type here
        def build_result(s:str,r: List[str]=r) -> List[str]:
            r.append(s)
            return r
        if writer is None:
            return "\n".join(log_fn(writer=build_result, **kw_args))
        return log_fn(writer=writer, **kw_args)
    #f write_string - writer callable to just write the string
    def write_string(self, writer:Writer, s:str) -> Any:
        return writer(s)
    #f write_multiline - writer callable to multiple lines with different indents
    def write_multiline(self, writer:Writer, s:str, initial_indent:str="", extra_indent:str="> ") -> None:
        sl = s.split("\n")
        if sl[-1]=="": sl=sl[:-1]
        i = initial_indent
        for l in sl:
            writer(i+l)
            i = initial_indent + extra_indent
            pass
        pass
    #f dump - write out the log to a file
    def dump(self, file:IO[str]=sys.stdout, suffix:str="\n") -> None:
        def writer(s:str)->None:
            file.write(s+suffix)
            pass
        for e in self.iter():
            self.write_entry(e,writer)
            pass
        pass
    pass
