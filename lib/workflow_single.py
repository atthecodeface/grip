#a Imports
from .workflow import Workflow
from .git import *
from .exceptions  import *

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
    def install_hooks(self):
        raise Exception("install_hooks not implemented for %s"%self.name)
    def commit(self):
        reason = self.git_repo.is_modified(self.options, log=self.log)
        if reason is not None:
            self.verbose.info("Repo %s is modified (%s) - attempting a commit"%(self.git_repo.get_name(), reason.get_reason()))
            self.git_repo.commit(log=self.log)
            pass
        return self.check_git_repo_is_upstreamed()
    def merge(self, force=False):
        reason = self.git_repo.is_modified(self.options, log=self.log)
        if reason is not None:
            raise WorkflowError("Git repo '%s' is modified (%s)"%(self.git_repo.get_name(), reason.get_reason()))
        reason = self.git_repo.rebase(self.options, other_branch="upstream", log=self.log)
        if reason is not None:
            raise WorkflowError("Git repo '%s' failed to merge (%s)"%(self.git_repo.get_name(), reason.get_reason()))
        return True
    def prepush(self):
        """
        Before a branch can be pushed it must be a descendant of upstream
        Hence upstream hash must be an ancestor of WIP.

        Then a git push --dry-run can be performed - if that is okay, we are set
        """
        self.check_git_repo_is_descendant()
        self.git_repo.push(dry_run=True, log=self.log, repo=self.git_repo.upstream_origin, ref="HEAD:%s"%(self.git_repo.upstream_push_branch))
        return True
    def push(self):
        """
        prepush MUST have been run recently
        If the push succeeds, then upstream must be at head
        """
        self.git_repo.push(dry_run=False, log=self.log, repo=self.git_repo.upstream_origin, ref="HEAD:%s"%(self.git_repo.upstream_push_branch))
        self.git_repo.change_branch_ref(log=self.log, branch_name="upstream", ref=self.grip_repo.branch_name)
        return True
    pass
