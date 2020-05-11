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
