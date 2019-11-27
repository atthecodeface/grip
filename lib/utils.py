import sys, os

def fatal_error(string, exit_value=1):
    print(string, file=sys.stderr)
    sys.exit(exit_value)
    pass

def options_value(options, key, env=None, default=None):
    if options is not None:
        if hasattr(options, key):
            value = getattr(options, key)
            if value is not None:
                return value
            pass
        pass
    if env is not None:
        if env in os.environ:
            return os.environ[env]
        pass
    return default

