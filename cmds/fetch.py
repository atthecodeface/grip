import os
import re
import lib.repo
from lib.command import GripCommandBase, ParsedCommand
from lib.options import Options
from typing import Optional
class fetch(GripCommandBase):
    """
    Fetch changes to the grip repo
    """
    names = ["fetch"]
    # command_options = {}
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo()
        self.grip_repo.fetch()
        return 0

class update(GripCommandBase):
    """
    Update upstream and WIP in to WIP for the grip repo
    """
    names = ["update"]
    command_options = {
                    ("--interactive",):{"action":"store_true", "dest":"interactive",  "default":False, "help":"Use interactive git rebase"},
    }
    def execute(self, cmd:ParsedCommand) -> Optional[int]:
        self.get_grip_repo()
        self.grip_repo.update()
        return 0

    
