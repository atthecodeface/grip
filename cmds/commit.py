import os
import re
import lib.command
import lib.repo
class commit(lib.command.GripCommandBase):
    """
    Commit changes to the grip repo
    """
    names = ["commit"]
    command_options = {
    }
    def execute(self, prog, parser, command_name, options, args):
        grip_repo = lib.repo.GripRepo(path=os.path.abspath(os.getcwd()))
        grip_repo.commit(options)
        pass
