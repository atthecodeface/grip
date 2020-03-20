#a Imports
from .workflow import Workflow

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
    def commit(self, grip_repo, git_repo):
        if not git_repo.is_modified(): return True
        git_repo.commit()
        return True
    pass
