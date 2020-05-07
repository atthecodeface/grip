#a Imports
from typing import Optional, List, Callable, Tuple, Iterable, Any

#a Classes
#c Class log
class Log:
    entries : List[Tuple[Callable, dict]]
    tidy_fn : Optional[Callable]
    #f __init__
    def __init__(self):
        self.entries = []
        self.tidy_fn = None
        pass
    #f add_entry
    def add_entry(self, log_fn : Callable, **kwargs):
        self.entries.append((log_fn,kwargs))
        pass
    #f set_tidy
    def set_tidy(self, tidy_fn):
        """
        Set the 'tidy' function to be called when user tidies logs up

        This may write, for example, write a log to a logfile
        """
        self.tidy_fn = tidy_fn
        pass
    #f tidy
    def tidy(self):
        if self.tidy_fn: self.tidy_fn()
        pass
    #f iter - iterate over entries
    def iter(self) -> Iterable[Tuple[Callable, dict]]:
        for e in self.entries:
            yield(e)
            pass
        pass
    #f add_entry
    def add_entry_string(self, s:str):
        self.add_entry(self.write_string,s=s)
        pass
    #f write_entry
    def write_entry(self, e:Tuple[Callable, dict], writer=None):
        (log_fn, kw_args)=e
        r : List = []
        def build_result(s,r=r) -> List:
            r.append(s)
            return r
        if writer is None:
            return "\n".join(log_fn(writer=build_result, **kw_args))
        return log_fn(writer=writer, **kw_args)
    #f write_string - writer callable to just write the string
    def write_string(self, writer:Callable[[str], Any], s:str):
        return writer(s)
    #f write_multiline - writer callable to multiple lines with different indents
    def write_multiline(self, writer, s, initial_indent="", extra_indent="> "):
        s = s.split("\n")
        if s[-1]=="": s=s[:-1]
        i = initial_indent
        for l in s:
            writer(i+l)
            i = initial_indent + extra_indent
            pass
        return
    #f dump - write out the log to a file
    def dump(self, file, suffix="\n"):
        def writer(s):
            file.write(s+suffix)
            pass
        for e in self.iter():
            self.write_entry(e,writer)
            pass
        pass
    pass
