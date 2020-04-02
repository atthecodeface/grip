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
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.commit(options)
        pass
