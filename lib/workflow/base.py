#a Imports
from typing import Type, Dict, List, Sequence, Any, Iterable, Tuple, Set, Optional
from ..options import Options
from ..log import Log
from ..verbose import Verbose
from ..exceptions import *
from ..git import Repository as GitRepository, branch_upstream, branch_remote_of_upstream, branch_head

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..grip import Toplevel
    from ..repo import Repository, GripRepository

#a Classes
#c Workflow - base class for workflows
class Workflow(object):
    name      : str = "Base workflow class - must be subclassed"
    permitted : bool = False
    options   : Options
    git_repo  : GitRepository
    log       : Log
    verbose   : Verbose
    toplevel  : 'Toplevel'

    git_repo_cs : str
    git_upstream_cs : str
    git_common_cs : str
    grip_config_upstream_cs : str
    grip_config_common_cs : str

    #f __init__
    def __init__(self, toplevel:'Toplevel', git_repo: GitRepository, repo:'Repository'):
        self.toplevel = toplevel
        self.git_repo  = git_repo
        self.repo    = repo
        self.options = toplevel.options
        self.log     = toplevel.log
        self.verbose = toplevel.verbose
        pass

    #f set_grip_config_cs
    def set_grip_config_cs(self, upstream_cs:str, common_cs:str) -> None:
        self.grip_config_upstream_cs = upstream_cs
        self.grip_config_common_cs   = common_cs
        pass
        
    #f get_git_repo_cs
    def get_git_repo_cs(self) -> None:
        self.git_repo_cs      = self.git_repo.get_cs()
        self.git_upstream_cs  = self.git_repo.get_cs(branch_name=branch_upstream)
        self.git_common_cs    = self.git_repo.get_common_ancestor(branch_upstream,"HEAD")
        pass
    
    #f get_branch_name
    def get_branch_name(self) -> str:
        return self.toplevel.get_branch_name()

    #f install_hooks
    def install_hooks(self) -> None:
        """
        Install any hooks required in the subrepos?
        """
        raise Exception("install_hooks not implemented for workflow %s"%self.name)

    #f get_repo_workflow_string
    def get_repo_workflow_string(self) -> str:
        return "Repo (%s) %s"%(self.name, self.git_repo.get_name())

    #f status
    def status(self) -> bool:
        """
        Report status of a git repo given a workflow

        Return False if could not be done
        """
        raise Exception("status not implemented for workflow %s"%self.name)
    #f status_as_grip
    def status_as_grip(self) -> bool:
        """
        Report status of a git repo given a workflow

        Return False if could not be done
        """
        raise Exception("status not implemented for workflow %s"%self.name)
    #f fetch
    def fetch(self, **kwargs:Any) -> bool:
        self.verbose.info("Fetching %s"%(self.get_repo_workflow_string()))
        output = self.git_repo.fetch()
        if len(output)>0:print(output)
        current_cs = self.git_repo.get_cs(branch_name=branch_upstream)
        fetched_cs = self.git_repo.get_cs(branch_name=branch_remote_of_upstream)
        self.git_repo.change_branch_ref(branch_name=branch_upstream, ref=fetched_cs)
        self.verbose.message("Repo '%s' %s stream branch now at %s (was at %s)"%(self.git_repo.get_name(), branch_upstream, fetched_cs, current_cs))
        return True
    #f update
    def update(self, **kwargs:Any) -> bool:
        """
        Update a git_repo with upstream using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("update not implemented for workflow %s"%self.name)
    #f update_as_grip
    def update_as_grip(self, **kwargs:Any) -> bool:
        """
        Update a git_repo with upstream using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("update not implemented for workflow %s"%self.name)
    #f commit
    def commit(self) -> bool:
        """
        Commit a git_repo using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("commit not implemented for workflow %s"%self.name)
    #f merge
    def merge(self, **kwargs:Any) -> bool:
        """
        Merge a git_repo with upstream using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("merge not implemented for workflow %s"%self.name)
    #f prepush
    def prepush(self) -> bool:
        """
        Prepare to push a git_repo upstream using the workflow
        This may be a merge; it may be nothing

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("prepush not implemented for workflow %s"%self.name)
    #f push
    def push(self) -> bool:
        """
        Push a git_repo upstream using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("push not implemented for workflow %s"%self.name)
    #f how_git_repo_upstreamed
    def how_git_repo_upstreamed(self) -> int:
        """
        Return 0 if git repo matches upstream
        Return 1 if git repo is descendant of upstream (upstream is common ancestor)
        Return -1 if git repo is ancestor of upstream (git repo is common ancestor)
        Return -2 if neither is the common ancestor (both have changed)
        """
        self.get_git_repo_cs()
        if self.git_repo_cs    == self.git_upstream_cs: return 0
        if self.git_common_cs  == self.git_repo_cs: return -1
        if self.git_common_cs  == self.git_upstream_cs: return 1
        return -2 # both have changed since common

    #f check_git_repo_is_descendant
    def check_git_repo_is_descendant(self) -> bool:
        how = self.how_git_repo_upstreamed()
        if how in [-1, -2]:
            raise WorkflowError("%s is at cs %s which is not a descendant of '%s' branch - have they been merged?"%(self.get_repo_workflow_string(), self.git_repo_cs, branch_upstream))
        if how==0:
            self.verbose.info("%s is at same cs as '%s' branch"%(self.get_repo_workflow_string(), branch_upstream))
            return True
        self.verbose.info("%s is a descendant of '%s' branch (at cs %s)"%(self.get_repo_workflow_string(), branch_upstream, self.git_repo_cs))
        return True
    
    #f check_git_repo_is_upstreamed
    def check_git_repo_is_upstreamed(self, exception_if_not:bool=True) -> bool:
        if self.how_git_repo_upstreamed() in [1, -2]:
            msg = "%s is at cs %s which is not an ancestor of '%s' branch"%(self.get_repo_workflow_string(), self.git_repo_cs, branch_upstream)
            self.verbose.warning(msg)
            if exception_if_not:
                raise WorkflowError(msg)
            return False
        self.verbose.info("%s is at cs %s - which is an ancestor of '%s' branch"%(self.get_repo_workflow_string(), self.git_repo_cs, branch_upstream))
        return True
    
    #f get_subclasses
    @classmethod
    def get_subclasses(cls, so_far:Optional[Set[Type['Workflow']]]=None) -> Iterable[Type['Workflow']]:
        if so_far is None: so_far=set()
        for subclass in cls.__subclasses__():
            if subclass not in so_far:
                so_far.add(subclass)
                yield subclass
                subclass.get_subclasses(so_far)
                pass
            pass
        pass


