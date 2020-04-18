#a Imports
import sys, os, re
import argparse
import traceback
import lib.utils
import lib.oscommand
from .hookable import Hookable
from .exceptions import *
from .verbose import Verbose
from .repo import GripRepo

#a Classes
#c Options
class UnknownOption(Exception):pass
class Options(object):
    verbose = False
    help = False
    show_log = False
    quiet = False
    def __init__(self):
        pass
    def has(self, n):
        return hasattr(self,n)
    def get(self, n, default=UnknownOption):
        if self.has(n): return getattr(self,n)
        if default is UnknownOption: raise UnknownOption("Option %s unknown"%n)
        return default
    def _validate(self):
        if type(self.verbose)==bool:
            verbose = Verbose()
            if self.verbose:     verbose.set_level(Verbose.level_verbose)
            if not self.verbose: verbose.set_level(Verbose.level_error)
            self.verbose = verbose
            pass
        elif type(self.verbose)==int:
            self.verbose = Verbose(level=self.verbose)
            pass
        pass
    def dump(self):
        for k in dir(self):
            print(k,self.get(k))
            pass
    
#c GripCommandBase
class GripCommandBase(Hookable):
    """
    This is the base class for all grip commands

    The docstring (this bit) is used for the help
    """
    #v Class properties
    names = []
    base_options = {("-h", "--help")   :{"action":"store_true", "dest":"help",     "default":False, "help":"show the list of commands and options", },
                    ("-v", "--verbose"):{"action":"store_true", "dest":"verbose",  "default":False},
                    ("--show-log",)    :{"action":"store_true", "dest":"show_log", "default":False},
                    ("-Q", "--quiet")  :{"action":"store_true", "dest":"quiet",    "default":False},
                    }
    command_options = {}

    #f get_all
    @classmethod
    def get_all(cls):
        cmds = cls.__subclasses__()
        cls.invoke_hooks(cls,"get_commands",cmds=cmds)
        return cmds

    #f command_of_name
    @classmethod
    def command_of_name(cls, name):
        for c in cls.get_all():
            for n in c.names:
                if name == n:
                    return c
                pass
            pass
        return None

    #f __init__
    def __init__(self, prog, command_name, options, args):
        if command_name is None:
            command_name=""
            pass
        else:
            command_name = command_name+" "
            pass
        self.loggers = []
        self.invocation = prog+" "+command_name+(" ".join(args))
        self.options = options
        pass
    
    #f parser_add_options
    def parser_add_options(self, parser, option_dict):
        """
        Invoked by a parse_command to add additional parser arguments base on an options dictionary
        """
        for (options, opt_args) in option_dict.items():
            if len(options)==2:
                parser.add_argument(options[0], options[1], **opt_args)
                pass
            else:
                parser.add_argument(options[0], **opt_args)
                pass
            pass
        pass

    #f parse_command
    def parse_command(self, prog, parser, command_name, options, args):
        """
        Invoked for toplevel 'grip ...', and for subcommands

        For toplevel, parser=command_name=options=None
        For subcommands these come from the parent parser
        """
        if options is None:
            options = Options()
            pass
        if parser is None:
            parser = argparse.ArgumentParser(prog=prog, add_help=False) # add_help=False as parent has -h
            self.parser_add_options(parser, self.base_options)
            pass
        else:
            prog = "%s %s"%(prog, command_name)
            parser = argparse.ArgumentParser(prog=prog, parents=[parser], add_help=False) # add_help=False as parent has -h
            pass
        cmd_parser = argparse.ArgumentParser(prog=prog, parents=[parser], add_help=False)
        self.parser_add_options(cmd_parser, self.command_options)
        options = cmd_parser.parse_args(args, namespace=options)
        options._validate()
        self.invoke_hooks("command_options", prog=prog, parser=cmd_parser, command_name=command_name, options=options, args=args)
        return (prog, parser, options, lib.utils.options_value(options,"args",default=[]))

    #f print_help
    def print_help(self):
        print("")
        print("Available grip commands are:\n%s" % "\n".join([k for k in commands.keys()]))
        pass

    #f get_grip_repo
    def get_grip_repo(self, **kwargs):
        self.grip_repo = GripRepo(invocation=self.invocation, options=self.options, **kwargs)
        self.add_logger(self.grip_repo.log)
        pass
    
    #f add_logger
    def add_logger(self, log):
        """
        Add a logger that is a log.Log class instance
        """
        self.loggers.append(log)
        pass
    
    #f show_logs
    def show_logs(self, file):
        """
        Write logs to file
        """
        for l in self.loggers:
            l.dump(file)
            pass
        pass
    
    #f tidy_logs
    def tidy_logs(self):
        """
        Tidy up logs
        """
        for l in self.loggers:
            l.tidy()
            pass
        pass
    
    #f invoke
    def invoke(self, prog, parser, command_name, options, args):
        command_cls = GripCommandBase.command_of_name(command_name)
        if command_cls is None: parser.error("Unknown command \"%s\"" % command_name)

        command = None
        try:
            command = command_cls(prog, command_name, options, args)
            (prog, parser, options, args) = command.parse_command(prog, parser, command_name, options, args)
            result = command.execute(prog, parser, command_name, options, args)
            command.tidy_logs()
            if options.show_log:
                command.show_logs(sys.stdout)
                pass
            if result:
                sys.exit(result)
                pass
            else:
                sys.exit(0)
                pass
            pass
        except GripException as e:
            command.tidy_logs()
            print("%s: %s" % (e.grip_type, str(e)), file=sys.stderr)
            if command is not None:
                if (command.options.get("show_log",False)): command.show_logs(sys.stderr)
                pass
            sys.exit(4)
        except lib.oscommand.OSCommand.Error as e:
            command.tidy_logs()
            print("Error from shell command %s" % str(e), file=sys.stderr)
            if options.verbose:
                traceback.print_exc()
                pass
            sys.exit(127)
            pass
        except Exception as e:
            command.tidy_logs()
            raise e
        pass
    #f All done
    pass

#c GripCommand
class GripCommand(GripCommandBase):
    """
    grip [options] <command> [<command options>] [<command arguments>]

    """
    names = []
    command_options = {("args",): {"nargs":argparse.REMAINDER, "help":'command to perform'},
                    }

#a Help
class Help(GripCommandBase):
    """
    grip [options] <command> [<command options>] [<command arguments>]

    use 'grip commands' to list the available commands
    """
    names = ["help"]
    command_options = {("args",): {"nargs":argparse.REMAINDER, "help":'command to perform'},
                    }
    def execute(self, prog, parser, command_name, options, args):
        command = self
        if len(args)>0:
            command_name = args[0]
            command = GripCommandBase.command_of_name(command_name)
            if command is None: parser.error("Unknown command \"%s\"" % command_name)
            pass
        print(command.__doc__.lstrip())
        pass
    pass

#a Commands
class Commands(GripCommandBase):
    """
    Provide a list of commands.
    """
    names = ["commands"]
    def execute(self, prog, parser, command_name, options, args):
        commands = GripCommandBase.get_all()
        command_names = []
        for n in commands:
            command_names.append(" ".join(n.names))
            pass
        print("Grip supports the following commands: \n%s\n" % "\n".join([k for k in sorted(command_names)]))
        print("Type \"grip help <command>\" for more help on any command.")
        pass
    pass
