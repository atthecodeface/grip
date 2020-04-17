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
        self.grip_repo.commit()
        pass

class merge(lib.command.GripCommandBase):
    """
    Merge upstream and WIP in to WIP for the grip repo
    """
    names = ["merge"]
    command_options = {
                    ("--ignore-untracked",):{"action":"store_true", "dest":"ignore_untracked",  "default":False, "help":"Ignore untracked files in git repositories in appropriate workflows"},
                    ("--interactive",):{"action":"store_true", "dest":"interactive",  "default":False, "help":"Use interactive git rebase"},
    }
    def execute(self, prog, parser, command_name, options, args):
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.merge()
        pass
    
class prepublish(lib.command.GripCommandBase):
    """
    Check if subrepos are ready to publish
    """
    names = ["prepublish"]
    command_options = {
    }
    def execute(self, prog, parser, command_name, options, args):
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.publish(prepush_only=True)
        pass
    
class publish(lib.command.GripCommandBase):
    """
    Attempt to push subrepos
    """
    names = ["publish"]
    command_options = {
    }
    def execute(self, prog, parser, command_name, options, args):
        self.get_grip_repo(path=os.path.abspath(os.getcwd()))
        self.grip_repo.publish(prepush_only=False)
        pass
    
