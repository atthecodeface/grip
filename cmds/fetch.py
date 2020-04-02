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
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.fetch(options)
        pass
