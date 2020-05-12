#a Imports
import sys, os, re
import argparse
import traceback
from pathlib import Path

from .os_command import OSCommand # for OSCommand.Error
from .hookable import Hookable
from .exceptions import *
from .verbose import Verbose
from .log import Log
from .options import Options
from typing import Type, Dict, List, Sequence, Any, Optional, Union, Tuple, IO
from .grip import Toplevel

Parser = argparse.ArgumentParser
ParserOptions = Dict[Tuple[str, ...], Dict[str, object]]
#a Classes
#c ParsedCommand
class ParsedCommand(object):
    """
    In essence this is a typed namespace for a parsed command, used in execute
    """
    def __init__(self, command:'GripCommandBase', args:List[str]):
        self.command = command
        self.args = args
        pass
    pass

#c GripCommandBase
class GripCommandBase(Hookable):
    """
    This is the base class for all grip commands

    The docstring (this bit) is used for the help
    """
    #v Class properties
    names : List[str] # Type['GripCommandBase']]= []
    base_options : Dict[Tuple[str, ...], Dict[str, object]]
    base_options = {("-h", "--help")     :{"action":"store_true", "dest":"help",         "default":False, "help":"show the list of commands and options", },
                    ("-v", "--verbose")  :{"action":"store_true", "dest":"verbose",      "default":False},
                    ("--show-log",)      :{"action":"store_true", "dest":"show_log",     "default":False},
                    ("--debug-config",)  :{"action":"store_true", "dest":"debug_config", "default":False, "help":"dump the complete configuration to the screen once it has been read"},
                    ("--grip-path",)     :{                       "dest":"grip_path",    "default":None, "help":"path to somewhere with the grip repository (default is working directory)"},
                    ("-Q", "--quiet")    :{"action":"store_true", "dest":"quiet",        "default":False},
                    }
    command_options : ParserOptions = {}
    #t Instance types
    prog       : str
    invocation : str
    parser     : argparse.ArgumentParser
    options    : Options
    loggers    : List[Log]
    #f get_all
    @classmethod
    def get_all(cls) -> List[Type['GripCommandBase']]:
        cmds = cls.__subclasses__()
        cls.class_invoke_hooks(hookname="get_commands",cmds=cmds)
        return cmds

    #f command_of_name
    @classmethod
    def command_of_name(cls, name:str)->Optional[Type['GripCommandBase']]:
        for c in cls.get_all():
            for n in c.names:
                if name == n:
                    return c
                pass
            pass
        return None

    #f __init__
    def __init__(self, command_name:str, parent:Optional['GripCommandBase']=None, args:List[str]=[]):
        if parent is None: # Called from toplevel grip
            self.options = Options()
            self.parser = argparse.ArgumentParser(prog=command_name, add_help=False) # add_help=False as parent has -h
            self.parser_add_options(self.base_options)
            self.prog = os.path.basename(command_name)
            self.loggers = []
            pass
        else:
            self.options = parent.options
            parser_prog = "%s %s"%(parent.prog, command_name)
            self.parser = argparse.ArgumentParser(prog=parser_prog, parents=[parent.parser], add_help=False) # add_help=False as parent has -h
            self.prog = parser_prog
            self.loggers = parent.loggers
            pass
        self.invocation = self.prog+(" ".join(args))
        pass

    #f parser_add_options
    def parser_add_options(self, option_dict:ParserOptions) -> None:
        """
        Invoked by a parse_command to add additional parser arguments base on an options dictionary
        """
        for (options, opt_args) in option_dict.items():
            if len(options)==2:
                self.parser.add_argument(options[0], options[1], **opt_args) # type:ignore
                pass
            else:
                self.parser.add_argument(options[0], **opt_args) # type:ignore
                pass
            pass
        pass

    #f parse_command - invoked from grip and from invoke
    def parse_command(self, args:List[str]) -> ParsedCommand:
        """
        Invoked for toplevel 'grip ...', and for subcommands

        For toplevel, parser=command_name=options=None
        For subcommands these come from the parent parser
        """
        # cmd_parser = argparse.ArgumentParser(prog=self.prog, parents=[self.parser], add_help=False)
        # self.parser_add_options(cmd_parser, self.command_options)
        # options = cmd_parser.parse_args(args, namespace=options)
        self.parser_add_options(self.command_options)
        self.parser.parse_args(args, namespace=self.options)
        self.options._validate()
        self.invoke_hooks("command_options", command=self)
        return ParsedCommand(self, self.options.get("args",default=[]))

    #f get_grip_repo
    def get_grip_repo(self, log:Optional[Log]=None, path:Optional[Path]=None, **kwargs:Any) -> None:
        if path is None:
            path_str =  self.options.get("grip_path",None)
            if path_str is None:
                path = Path(".").resolve()
                pass
            else:
                path = Path(path_str)
            pass
        if log is None: log = Log()
        self.add_logger(log)
        self.grip_repo = Toplevel(path=path, log=log, invocation=self.invocation, options=self.options, **kwargs)
        pass

    #f add_logger
    def add_logger(self, log:Log) -> None:
        """
        Add a logger that is a log.Log class instance
        """
        self.loggers.append(log)
        pass

    #f show_logs
    def show_logs(self, file:IO[str]) -> None:
        """
        Write logs to file
        """
        for l in self.loggers:
            l.dump(file)
            pass
        pass

    #f tidy_logs
    def tidy_logs(self) -> None:
        """
        Tidy up logs
        """
        for l in self.loggers:
            l.tidy()
            pass
        pass

    #f execute
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        raise Exception("Unimplemented execution of command")
    #f invoke_subcommand
    def invoke_subcommand(self, command_name:str, args:List[str]) -> None:
        """
        Invoke a subcommand of this command - invoked only by grip
        """
        command_cls = GripCommandBase.command_of_name(command_name)
        if command_cls is None:
            return self.parser.error("Unknown command \"%s\"" % command_name) # type:ignore

        command = command_cls(parent=self, command_name=command_name, args=args)
        try:
            parsed_command = command.parse_command(args)
            result = command.execute(parsed_command)
            command.tidy_logs()
            if self.options.show_log:
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
            self.tidy_logs()
            print("%s: %s" % (e.grip_type, str(e)), file=sys.stderr)
            if (self.options.get("show_log",False)): self.show_logs(sys.stderr)
            sys.exit(4)
        except OSCommand.Error as e:
            self.tidy_logs()
            print("Error from shell command %s" % str(e), file=sys.stderr)
            if self.options.verbose:
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
    names : List[str] = []
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
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        command : Optional[Type[GripCommandBase]] = self.__class__
        if len(cmd.args)>0:
            command_name = cmd.args[0]
            command = GripCommandBase.command_of_name(command_name)
            pass
        if command is None:
            return cmd.parser.error("Unknown command \"%s\"" % command_name) # type:ignore
        doc = "<Undocumented command>"
        if command.__doc__ is not None: doc=command.__doc__
        print(doc.lstrip())
        return None
    pass

#a Commands
class Commands(GripCommandBase):
    """
    Provide a list of commands.
    """
    names = ["commands"]
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        commands = GripCommandBase.get_all()
        command_names = []
        for n in commands:
            command_names.append(" ".join(n.names))
            pass
        print("Grip supports the following commands: \n%s\n" % "\n".join([k for k in sorted(command_names)]))
        print("Type \"grip help <command>\" for more help on any command.")
        return None
    pass
