#a Imports
from ..exceptions  import *
from ..log import Log
from ..options import Options
from ..verbose import Verbose
from typing import Any, Optional
from .base import Workflow
from ..git import Repository as GitRepository

#a Classes
#c Single workflow
class Single(Workflow):
    """
    The single workflow for git repositories in a grip repo is where pushing upstream
    must be to the specified branch.

    Editing and committing to the git repository is permitted.
    Pushing upstream requires a rebased merge of the local (unnamed) branch prior to the push.

    The checkout of a git repository at a particular CS will put HEAD at that CS, and it
    is detached from any branch.
    PROBABLY WE SHOULD NAME THE BRANCH.
    Any edits and then commits performed are on this new detached branch; a new commit
    extends this branch, and moves HEAD along.

    Merging is required before pushing. Merging is performed using
    "git pull --rebase origin <branch>"
    A push can only be performed if a merge has been completed.

    The grip repo state is updated with the cs of the post-merge, i.e. successfully pushed, repo
    """
    name = "single"
    #f install_hooks
    def install_hooks(self) -> None:
        raise Exception("install_hooks not implemented for %s"%self.name)
    #f status
    def status(self) -> bool:
        repo_string = self.get_repo_workflow_string()
        reason = self.git_repo.is_modified()
        if reason is None:
            (cs, cs_upstream, cmp) = self.how_git_repo_upstreamed()
            if cmp==0:
                self.verbose.info("%s matches 'upstream' (%s)"%(repo_string, cs))
                pass
            elif cmp>0:
                self.verbose.message("%s is unmodified (%s) but a descendant of 'upstream' (%s) - so pushable"%(repo_string, cs, cs_upstream))
                pass
            else:
                self.verbose.warning("%s is unmodified (%s) but an ancestor of 'upstream' (%s) - so needs a merge"%(repo_string, cs, cs_upstream))
                pass
            return True
        self.verbose.message("%s has %s"%(repo_string, reason.get_reason()))
        if not self.verbose.is_verbose(): return True
        print(self.git_repo.status())
        return True
    #f merge
    def merge(self, **kawrgs:Any) -> bool:
        reason = self.git_repo.is_modified()
        if reason is not None:
            raise WorkflowError("%s is modified (%s)"%(self.get_repo_workflow_string(), reason.get_reason()))
        reason = self.git_repo.rebase(other_branch="upstream")
        if reason is not None:
            raise WorkflowError("%s failed to merge (%s)"%(self.get_repo_workflow_string(), reason.get_reason()))
        return True
    #f commit
    def commit(self) -> bool:
        reason = self.git_repo.is_modified()
        if reason is not None:
            self.verbose.message("%s is modified (%s) - attempting a commit"%(self.get_repo_workflow_string(), reason.get_reason()))
            self.git_repo.commit()
            pass
        is_upstreamed = self.check_git_repo_is_upstreamed()
        self.verbose.error("%s is not upstreamed - perhaps a grip merge is required."%(self.get_repo_workflow_string()))
        return is_upstreamed
    #f prepush
    def prepush(self) -> bool:
        """
        Before a branch can be pushed it must be a descendant of upstream
        Hence upstream hash must be an ancestor of WIP.

        Then a git push --dry-run can be performed - if that is okay, we are set
        """
        self.check_git_repo_is_descendant()
        upstream = self.git_repo.get_upstream()
        if upstream is None:
            raise WorkflowError("%s cannot be pushed, it has no upstream"%(self.get_repo_workflow_string()))
        self.git_repo.push(dry_run=True, repo=upstream.get_origin(), ref="HEAD:%s"%(upstream.get_branch()))
        return True
    #f push
    def push(self) -> bool:
        """
        prepush MUST have been run recently
        If the push succeeds, then upstream must be at head
        """
        upstream = self.git_repo.get_upstream()
        if upstream is None:
            raise WorkflowError("%s cannot be pushed, it has no upstream"%(self.get_repo_workflow_string()))
        self.git_repo.push(dry_run=False, repo=upstream.get_origin(), ref="HEAD:%s"%(upstream.get_branch()))
        self.git_repo.change_branch_ref(branch_name="upstream", ref=self.get_branch_name())
        return True
    #f All done
    pass
