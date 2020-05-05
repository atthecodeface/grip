import sys
def info(options, msg):
    if options is None:return
    if options.verbose: print(msg)
    pass

class TermColors:
    plain      = "\033[0m"
    bold       = "\033[1m"
    underline  = "\033[4m"
    red        = "\033[91m"
    green      = "\033[92m"
    yellow     = "\033[93m"
    blue       = "\033[94m"
    magenta    = "\033[95m"
    cyan       = "\033[96m"

class Verbose:
    level_verbose = 0
    level_info = 1
    level_message = 2
    level_warning = 3
    level_error = 4
    level_fatal = 5
    colors = {level_verbose :TermColors.plain,
              level_info    :TermColors.green,
              level_message :TermColors.cyan,
              level_warning :TermColors.yellow,
              level_error   :TermColors.red,
              level_fatal   :(TermColors.bold + TermColors.red),
              }
    def __init__(self, level=1, file=sys.stdout, use_color=True):
        self.level = level
        self.file = file
        self.use_color = use_color
        pass
    def set_level(self, level):
        self.level = level
        pass
    def write(self, level, s):
        if self.level>level: return
        if self.use_color: s = self.colors[level] + s + TermColors.plain
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

