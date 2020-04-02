class Log:
    def __init__(self):
        self.entries = []
        self.tidy_fn = None
        pass
    def add_entry(self, log_fn, **kwargs):
        self.entries.append((log_fn,kwargs))
        pass
    def set_tidy(self, tidy_fn):
        """
        Set the 'tidy' function to be called when user tidies logs up

        This may write, for example, write a log to a logfile
        """
        self.tidy_fn = tidy_fn
        pass
    def tidy(self):
        if self.tidy_fn: self.tidy_fn()
        pass
    def iter(self):
        for e in self.entries:
            yield e
            pass
        pass
    def add_entry_string(self, s):
        self.add_entry(self.write_string,s=s)
        pass
    def write_entry(self, e, writer=None):
        (log_fn, kw_args)=e
        r = []
        def build_result(s,r=r):
            r.append(s)
            return r
        if writer is None:
            return "\n".join(log_fn(writer=build_result, **kw_args))
        return log_fn(writer=writer, **kw_args)
    def write_string(self, writer, s):
        return writer(s)
    def write_multiline(self, writer, s, initial_indent="", extra_indent="> "):
        s = s.split("\n")
        if s[-1]=="": s=s[:-1]
        i = initial_indent
        for l in s:
            writer(i+l)
            i = initial_indent + extra_indent
            pass
        return
    def dump(self, file, suffix="\n"):
        def writer(s):
            file.write(s+suffix)
            pass
        for e in self.iter():
            self.write_entry(e,writer)
            pass
        pass
    pass
