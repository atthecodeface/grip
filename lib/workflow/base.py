#a Imports
from typing import Type, Dict, List, Sequence, Any, Iterable, Tuple, Set
from ..options import Options
from ..log import Log
from ..verbose import Verbose
from ..exceptions import *
from ..git import Repository as GitRepository, branch_upstream, branch_remote_of_upstream, branch_head

from typing import TYPE_CHECKING
if TYPE_CHECKING: from ..grip import Toplevel

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
    #f __init__
    def __init__(self, toplevel:'Toplevel', git_repo: GitRepository):
        self.toplevel = toplevel
        self.git_repo  = git_repo
        self.options = toplevel.options
        self.log     = toplevel.log
        self.verbose = toplevel.verbose
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
    #f commit
    def commit(self) -> bool:
        """
        Commit a git_repo using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("commit not implemented for workflow %s"%self.name)
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
    #f check_git_repo_is_descendant
    def check_git_repo_is_descendant(self) -> bool:
        cs_history = self.git_repo.get_cs_history(branch_name=self.toplevel.get_branch_name())
        try:
            cs = self.git_repo.get_cs(branch_name=branch_upstream)
        except HowUnknownBranch as e:
            raise WorkflowError("%s"%str(e))
        if cs not in cs_history:
            raise WorkflowError("%s is not a descendant of '%s' which is at cs '%s' - have they been merged?"%(self.get_repo_workflow_string(), branch_upstream, cs))
        self.verbose.info("%s is a descendant of '%s' branch (at cs %s)"%(self.get_repo_workflow_string(), branch_upstream, cs))
        return True
    #f how_git_repo_upstreamed
    def how_git_repo_upstreamed(self) -> Tuple[str,str,int]:
        """
        Return 0 if git repo matches upstream
        Return 1 if git repo is descendant of upstream
        Return -1 if git repo is ancestor of upstream
        """
        cs = self.git_repo.get_cs()
        cs_upstream = self.git_repo.get_cs(branch_name=branch_upstream)
        if cs==cs_upstream: return (cs, cs_upstream, 0)
        try:
            cs_history = self.git_repo.get_cs_history(branch_name=branch_upstream)
        except HowUnknownBranch as e:
            raise WorkflowError("%s"%str(e))
        if cs in cs_history: return (cs, cs_upstream, -1)
        return (cs, cs_upstream, 1)
    #f check_git_repo_is_upstreamed
    def check_git_repo_is_upstreamed(self, exception_if_not:bool=True) -> bool:
        (cs, cs_upstream, cmp) = self.how_git_repo_upstreamed()
        if cmp>0:
            self.verbose.warning("%s is at cs '%s' which is not an ancestor of '%s' branch"%(self.get_repo_workflow_string(), cs, branch_upstream))
            if exception_if_not:
                raise WorkflowError("%s is not part of '%s'"%(self.get_repo_workflow_string(), branch_upstream))
            return False
        self.verbose.info("%s is at cs %s - which is an ancestor of '%s' branch"%(self.get_repo_workflow_string(), cs, branch_upstream))
        return True
    #f get_subclasses
    @classmethod
    def get_subclasses(cls, so_far:Set[Type['Workflow']]=set()) -> Iterable[Type['Workflow']]:
        for subclass in cls.__subclasses__():
            if subclass not in so_far:
                so_far.add(subclass)
                yield subclass
                subclass.get_subclasses(so_far)
                pass
            pass
        pass


