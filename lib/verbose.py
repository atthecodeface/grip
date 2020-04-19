import sys
def info(options, msg):
    if options is None:return
    if options.verbose: print(msg)
    pass

class Verbose:
    level_verbose = 0
    level_info = 1
    level_message = 2
    level_warning = 3
    level_error = 4
    level_fatal = 5
    def __init__(self, level=1, file=sys.stdout):
        self.level = level
        self.file = file
        pass
    def set_level(self, level):
        self.level = level
        pass
    def write(self, level, s):
        if self.level>level: return
        print(s, file=self.file)
        return
    def is_verbose(self): return self.level<=self.level_verbose
    def verbose(self, s):
        return self.write(self.level_verbose, s)
    def info(self, s):
        return self.write(self.level_info, s)
    def message(self, s):
        return self.write(self.level_message, s)
    def warning(self, s):
        return self.write(self.level_warning, s)
    def error(self, s):
        return self.write(self.level_error, s)
    def fatal(self, s):
        return self.write(self.level_fatal, s)
        
