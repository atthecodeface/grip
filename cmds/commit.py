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
                    ("--ignore-untracked",):{"action":"store_true", "dest":"ignore_untracked",  "default":False, "help":"Ignore untracked files in git repositories in appropriate workflows"},
                    ("--ignore-modified",):{"action":"store_true", "dest":"ignore_modified",  "default":False, "help":"Ignore modified files in git repositories in appropriate workflows"},
    }
    def execute(self, prog, parser, command_name, options, args):
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.commit(options)
        pass
