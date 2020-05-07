#a Imports
import os, time
from typing import Type, List, Dict, Iterable, Optional, Any
from .git import GitRepo, branch_upstream, branch_head
from .descriptor.stage import Dependency as StageDependency
from .descriptor.grip import Descriptor as GripRepoDescriptor
from .config.file import ConfigFile as GripRepoConfig
from .state.file  import StateFile as GripRepoState
from .workflow import Workflow
from .log import Log
from .verbose import Verbose
from .exceptions import *

#a Classes
#c Repository class
class Repository(object):
    #f Documentation
    """
    This class manages a git repository that may be a simple git
    subrepository or the toplevel repository.

    It ties together a grip subrepository description with a checked-out
    git repository, using a particular workflow.


    It provides methods for repository management such as:

    * status  - report status of the repository
              - branch must be WIP
    * commit  - commit all changes in the repository
              - branch must be WIP
    * fetch   - fetch updates (to local 'upstream' branch)
    * merge   - merge branch with 'upstream' branch
              - branch must be WIP
              - must be unmodified
    * prepush - verify WIP branch is ready to be pushed
              - branch must be WIP
              - must be unmodified
              - may not need to be merged - that depends on workflow
    * push    - push WIP to the push upstream
              - branch must be WIP
              - must be unmodified
              - may not need to be merged - that depends on workflow
    """
    name      : str
    toplevel  : Any # Cannot use Type['Toplevel'] as that would be recursive libraries
    git_repo  : GitRepo
    parent    : Optional[Type['Repository']]
    workflow  : Workflow
    subrepos  : List[Type['Repository']]
    #f __init__
    # note that specifying parent to be Type['Repository'] breaks mypy in the subrepos.append(child)
    def __init__(self, name:str, grip_repo, parent, git_repo:GitRepo, repo_desc:GripRepoDescriptor):
        """
        """
        self.name = name
        self.toplevel = grip_repo
        self.parent = parent
        self.git_repo = git_repo
        self.repo_desc = repo_desc
        w : Type[Workflow] = repo_desc.workflow
        self.workflow = w(grip_repo, git_repo)
        self.subrepos = []
        if parent: parent.add_child(self)
        pass
    #f add_child
    def add_child(self, child : Type['Repository']):
        self.subrepos.append(child)
        pass
    #f iter_subrepos
    def iter_subrepos(self) -> Iterable[Type['Repository']]:
        for s in self.subrepos:
            yield(s)
            pass
        pass
    #f install_hooks
    def install_hooks(self):
        for sr in self.subrepos:
            sr.install_hooks()
            pass
        pass
    #f status
    def status(self):
        for sr in self.subrepos: sr.status()
        try:
            s = "Getting status of repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.workflow.status()
            pass
        except Exception as e:
            raise(e)
        pass
    #f commit
    def commit(self):
        for sr in self.subrepos: sr.commit()
        try:
            s = "Commiting repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.message(s)
            okay = self.workflow.commit()
            if not okay: raise(Exception("Commit for repo '%s' not permitted"%self.name))
            cs = self.get_cs()
            self.grip_repo.add_log_string("Repo '%s' at commit hash '%s'"%(self.name, cs))
            pass
        except Exception as e:
            raise(e)
        pass
    #f fetch
    def fetch(self):
        for sr in self.subrepos: sr.fetch()
        try:
            s = "Fetching repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.fetch()
            if not okay: raise(Exception("Fetch for repo '%s' not permitted"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f merge
    def merge(self, force=False):
        for sr in self.subrepos: sr.merge()
        try:
            s = "Merging repo '%s' with workflow '%s' (force %s)"%(self.name, self.workflow.name, str(force))
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.merge(force=force)
            if not okay: raise(Exception("Merge for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f prepush
    def prepush(self):
        for sr in self.subrepos: sr.prepush()
        try:
            s = "Prepushing repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.prepush()
            if not okay: raise(Exception("Prepush for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f push
    def push(self):
        for sr in self.subrepos: sr.push()
        try:
            s = "Pushing repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.push()
            if not okay: raise(Exception("Push for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f get_cs
    def get_cs(self):
        return self.git_repo.get_cs()
    #f All done
    pass

