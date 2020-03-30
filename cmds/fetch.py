import os
import re
import lib.command
import lib.repo
class fetch(lib.command.GripCommandBase):
    """
    Fetch changes to the grip repo
    """
    names = ["fetch"]
    command_options = {
    }
    def execute(self, prog, parser, command_name, options, args):
        grip_repo = lib.repo.GripRepo(path=os.path.abspath(os.getcwd()))
        grip_repo.fetch(options)
        pass
