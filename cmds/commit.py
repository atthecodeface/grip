import os
from lib.command import GripCommandBase, ParsedCommand
from lib.options import Options
from typing import Optional, List

class commit(GripCommandBase):
    """
    Commit changes to the grip repo
    """
    names = ["commit"]
    command_options = {
                    ("--ignore-untracked",):{"action":"store_true", "dest":"ignore_untracked",  "default":False, "help":"Ignore untracked files in git repositories in appropriate workflows"},
                    ("--ignore-modified",):{"action":"store_true", "dest":"ignore_modified",  "default":False, "help":"Ignore modified files in git repositories in appropriate workflows"},
    }
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.commit()
        return 0

class merge(GripCommandBase):
    """
    Merge upstream and WIP in to WIP for the grip repo
    """
    names = ["merge"]
    command_options = {
                    ("--ignore-untracked",):{"action":"store_true", "dest":"ignore_untracked",  "default":False, "help":"Ignore untracked files in git repositories in appropriate workflows"},
                    ("--interactive",):{"action":"store_true", "dest":"interactive",  "default":False, "help":"Use interactive git rebase"},
    }
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.merge()
        return 0

class prepublish(GripCommandBase):
    """
    Check if subrepos are ready to publish
    """
    names = ["prepublish"]
    # command_options = {}
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.publish(prepush_only=True)
        return 0

class publish(GripCommandBase):
    """
    Attempt to push subrepos
    """
    names = ["publish"]
    # command_options = {}
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.publish(prepush_only=False)
        return 0

