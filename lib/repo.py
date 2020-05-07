#a Imports
import os, time
from typing import Type, List, Dict, Iterable, Optional, Any
from .git import Repository as GitRepository
from .descriptor import StageDependency as StageDependency
from .descriptor import RepositoryDescriptor
from .descriptor import GripDescriptor
from .config.file import ConfigFile as GripRepoConfig
from .state.file  import StateFile as GripRepoState
from .workflow import Workflow
from .log import Log
from .verbose import Verbose
from .exceptions import *

from typing import TYPE_CHECKING
if TYPE_CHECKING: from .grip import Toplevel

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
    name       : str
    toplevel   : Any # Cannot use Type['Toplevel'] as that would be recursive libraries
    git_repo   : GitRepository
    parent     : Optional['Repository']
    workflow   : Workflow
    subrepos   : List['Repository']
    #f __init__
    def __init__(self, name:str, grip_repo:'Toplevel', parent:Optional['Repository'], git_repo:GitRepository, workflow:Type[Workflow]):
        """
        """
        self.name = name
        self.toplevel = grip_repo
        self.parent = parent
        self.git_repo = git_repo
        self.workflow = workflow(grip_repo, git_repo)
        self.subrepos = []
        if parent: parent.add_child(self)
        pass
    #f add_child
    def add_child(self, child : 'Repository') -> None:
        self.subrepos.append(child)
        pass
    #f iter_subrepos
    def iter_subrepos(self) -> Iterable['Repository']:
        for s in self.subrepos:
            yield(s)
            pass
        pass
    #f install_hooks
    def install_hooks(self) -> None:
        for sr in self.subrepos:
            sr.install_hooks()
            pass
        pass
    #f status
    def status(self) -> bool:
        okay = True
        for sr in self.subrepos:
            okay = okay and sr.status()
            pass
        try:
            s = "Getting status of repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            okay = okay and self.workflow.status()
            pass
        except Exception as e:
            raise(e)
        return okay
    #f commit
    def commit(self) -> bool:
        okay = True
        for sr in self.subrepos:
            okay = okay and sr.commit()
            pass
        try:
            s = "Commiting repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            self.toplevel.verbose.message(s)
            okay = okay and self.workflow.commit()
            if not okay: raise(Exception("Commit for repo '%s' not permitted"%self.name))
            cs = self.get_cs()
            self.toplevel.add_log_string("Repo '%s' at commit hash '%s'"%(self.name, cs))
            pass
        except Exception as e:
            raise(e)
        return okay
    #f fetch
    def fetch(self) -> bool:
        okay = True
        for sr in self.subrepos:
            okay = okay and sr.fetch()
            pass
        try:
            s = "Fetching repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            self.toplevel.verbose.info(s)
            okay = okay and self.workflow.fetch()
            if not okay: raise(Exception("Fetch for repo '%s' not permitted"%self.name))
            pass
        except Exception as e:
            raise(e)
        return okay
    #f merge
    def merge(self, force:bool=False) -> bool:
        okay = True
        for sr in self.subrepos:
            okay = okay and sr.merge(force=force)
            pass
        try:
            s = "Merging repo '%s' with workflow '%s' (force %s)"%(self.name, self.workflow.name, str(force))
            self.toplevel.add_log_string(s)
            self.toplevel.verbose.info(s)
            okay = okay and self.workflow.merge(force=force)
            if not okay: raise(Exception("Merge for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        return okay
    #f prepush
    def prepush(self) -> bool:
        okay = True
        for sr in self.subrepos:
            okay = okay and sr.prepush()
            pass
        try:
            s = "Prepushing repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            self.toplevel.verbose.info(s)
            okay = okay and self.workflow.prepush()
            if not okay: raise(Exception("Prepush for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        return okay
    #f push
    def push(self) -> bool:
        okay = True
        for sr in self.subrepos:
            okay = okay and sr.push()
            pass
        try:
            s = "Pushing repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            self.toplevel.verbose.info(s)
            okay = okay and self.workflow.push()
            if not okay: raise(Exception("Push for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        return okay
    #f get_cs
    def get_cs(self) -> str:
        return self.git_repo.get_cs()
    #f All done
    pass

