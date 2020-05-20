#a Import
import os, sys, shlex
from pathlib import Path
import lib.repo
import lib.env
from lib.command import GripCommandBase, ParsedCommand
from lib.options import Options
from lib.types   import Documentation, DocumentationHeadedContent
from typing import Optional, Tuple, Any, cast

#a Commands classes
#c root
class root(GripCommandBase):
    """
    Find the root of the grip repository
    """
    names = ["root"]
    # command_options = { }
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(ensure_configured=False)
        print(self.grip_repo.get_root(),end='')
        return 0
    pass

class env(GripCommandBase):
    """
    Returns the grip environment (what would be placed in the grip env shell file).

    This is suitable to be used with "eval `grip env`"
    """
    names = ["env"]
    # command_options = {}
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo()
        for (k,v) in self.grip_repo.grip_env_iter():
            print('%s=%s; export %s'%(k,shlex.quote(v),k))
            pass
        return 0
    pass

#f show_documentation
from lib.verbose import TermColors
def show_documentation(doc:Documentation, indent:int=0) -> None:
    nl = False
    for d in doc:
        if nl: print()
        if type(d)==tuple:
            # d must be DocumentationHeadedContent = Tuple[str, List[DocumentationEntry]]
            # Help typing by asserting this
            de = cast(DocumentationHeadedContent, d)
            (n,v)=de
            pre_heading  = "\n"+(" "*indent)+TermColors.bold+TermColors.underline
            post_heading = TermColors.plain
            print("%s%s%s"%(pre_heading,n,post_heading))
            show_documentation(v, indent+1)
            nl = False
            pass
        else:
            # d must be str
            # Help typing by asserting this
            ds = cast(str, d)
            print(ds)
            nl = False
            pass
        pass
    pass

#c doc
class doc(GripCommandBase):
    """
    Prints the documentation

    If the repository has a configuration warning, such as from
    an undefined environment variable, then the return code will be 1

    With no warnings or errors the return code will be 0
    """
    names = ["doc"]
    # command_options = {}
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        warnings = []
        def f(e:Exception) -> Tuple[str]:
            warnings.append(str(e))
            ge = cast(lib.env.GripEnvValueError, e)
            ge.grip_env.get_root().add_values({ge.key:""})
            return ("",)
        self.get_grip_repo(ensure_configured=False, error_handler=lib.env.GripEnvValueError.error_handler(f))
        for w in warnings:
            self.grip_repo.verbose.warning(w)
            pass
        grip_repo_doc = self.grip_repo.get_doc()
        if self.grip_repo.is_configured():
            print("This is a configured grip repository, with a name of '%s', using configuration '%s'"%(self.grip_repo.get_name(), self.grip_repo.get_config_name()))
            pass
        else:
            print("This is an unconfigured grip repository, with a name of '%s'"%(self.grip_repo.get_name()))
            print("It supports the following configurations: %s"%(" ".join(self.grip_repo.get_configurations())))
            pass
        show_documentation(grip_repo_doc)
        if len(warnings)>0:
            return 1
        return 0
    pass

#c status
class status(GripCommandBase):
    """
    Get status
    """
    names = ["status"]
    # command_options = {}
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo()
        self.grip_repo.status()
        return 0
    pass
