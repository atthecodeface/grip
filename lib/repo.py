#a Imports
import os, time
from typing import Type, List, Dict, Iterable, Optional, Any
from .git import Repository as GitRepository, branch_upstream

from .descriptor import StageDependency as StageDependency
from .descriptor import RepositoryDescriptor
from .descriptor import GripDescriptor
from .configstate import ConfigFile as GripRepoConfig
from .configstate import StateFile as GripRepoState
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
    #t Property types
    name       : str
    toplevel   : Any # Cannot use Type['Toplevel'] as that would be recursive libraries
    git_repo   : GitRepository
    parent     : Optional['Repository']
    workflow   : Workflow
    subrepos   : List['Repository']
    is_grip_repo = False
    #f __init__
    def __init__(self, name:str, grip_repo:'Toplevel', parent:Optional['Repository'], git_repo:GitRepository, workflow:Type[Workflow]):
        """
        """
        self.name = name
        self.toplevel = grip_repo
        self.parent = parent
        self.git_repo = git_repo
        self.workflow = workflow(grip_repo, git_repo, self)
        self.subrepos = []
        if parent: parent.add_child(self)
        pass
    #f get_name
    def get_name(self) -> str:
        return self.name
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
        for sr in self.iter_subrepos():
            sr.install_hooks()
            pass
        pass
    #f set_grip_config_cs
    def set_grip_config_cs(self, upstream_cs:str, common_cs:str) -> None:
        self.workflow.set_grip_config_cs(upstream_cs=upstream_cs, common_cs=common_cs)
        pass
    #f set_subrepo_cs_set - only really needed for grip repositories
    def set_subrepo_cs_set(self) -> None:
        pass
    #f status
    def status(self) -> bool:
        self.set_subrepo_cs_set()
        okay = True
        for sr in self.iter_subrepos():
            okay = okay and sr.status()
            pass
        try:
            s = "Getting status of repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            if self.is_grip_repo:
                okay = okay and self.workflow.status_as_grip()
                pass
            else:
                okay = okay and self.workflow.status()
                pass
            pass
        except Exception as e:
            raise(e)
        return okay
    #f commit
    def commit(self) -> bool:
        self.set_subrepo_cs_set()
        okay = True
        for sr in self.iter_subrepos():
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
        self.set_subrepo_cs_set()
        okay = True
        for sr in self.iter_subrepos():
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
    #f update
    def update(self) -> bool:
        self.set_subrepo_cs_set()
        okay = True
        try:
            s = "Updating repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.toplevel.add_log_string(s)
            self.toplevel.verbose.info(s)
            if self.is_grip_repo:
                okay = okay and self.workflow.update_as_grip()
                pass
            else:
                okay = okay and self.workflow.update()
                pass
            if not okay: raise(Exception("Update for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        for sr in self.iter_subrepos():
            okay = okay and sr.update()
            pass
        return okay
    #f merge
    def merge(self, force:bool=False) -> bool:
        self.set_subrepo_cs_set()
        okay = True
        for sr in self.iter_subrepos():
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
        self.set_subrepo_cs_set()
        okay = True
        for sr in self.iter_subrepos():
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
        self.set_subrepo_cs_set()
        okay = True
        for sr in self.iter_subrepos():
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


#a GripRepository - subclass of Repository
class GripRepository(Repository):
    is_grip_repo = True
    #f get_config_state
    def get_config_state(self, branch:str) -> Any:
        toml_string  = self.git_repo.get_file_from_cs(self.toplevel.grip_path(self.toplevel.state_toml_filename), branch_upstream)
        state_file = GripRepoState(base=self.toplevel)
        state_file.read_toml_string(toml_string)
        config = state_file.select_config(self.toplevel.get_config_name())
        return config
    #f set_subrepo_cs_set
    def set_subrepo_cs_set(self) -> None:
        common_ancestor = self.git_repo.get_common_ancestor(branch_upstream,self.toplevel.get_branch_name())

        cfg_upstream  = self.get_config_state(branch_upstream)
        cfg_common    = self.get_config_state(common_ancestor)
        for sr in self.iter_subrepos():
            sr.set_grip_config_cs(upstream_cs = cfg_upstream.get_repo_cs(sr.name),
                                  common_cs   = cfg_common.get_repo_cs(sr.name))
            pass
        pass
    #f All done
    pass

