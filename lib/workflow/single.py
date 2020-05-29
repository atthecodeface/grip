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
            cmp = self.how_git_repo_upstreamed()
            if cmp==0:
                self.verbose.info("%s matches 'upstream' (%s)"%(repo_string, self.git_repo_cs))
                pass
            elif cmp>0:
                self.verbose.message("%s is unmodified (%s) but a descendant of 'upstream' (%s) - so pushable"%(repo_string, self.git_repo_cs, self.git_upstream_cs))
                pass
            else:
                self.verbose.warning("%s is unmodified (%s) 'upstream' (%s) is newer - so needs a merge"%(repo_string, self.git_repo_cs, self.git_upstream_cs))
                pass
            return True
        self.verbose.message("%s has %s"%(repo_string, reason.get_reason()))
        if not self.verbose.is_verbose(): return True
        print(self.git_repo.status())
        return True
    #f status_as_grip
    def status_as_grip(self) -> bool:
        """
        For all subrepos that have not changed in upstream grip config since our checkout
          If we have new ones then we should accept them if they are upstreamed
          If they are *ancestors* of that in grip config, then we have rewound
            but because upstream has not budge in this respect, this was deliberate
          
        """
        repo_string = self.get_repo_workflow_string()
        okay = True
        for sr in self.repo.iter_subrepos():
            srw = sr.workflow
            srw.get_git_repo_cs()
            if srw.grip_config_upstream_cs == srw.grip_config_common_cs:
                # Upstream CS is no changed since our checkout
                if srw.git_repo_cs == srw.grip_config_common_cs:
                    # No changes between our repo and the config - nothing to report
                    pass
                elif srw.git_repo_cs == srw.git_upstream_cs:
                    # Our CS is upstream tip but differs from checkout which is same as upstream condfig
                    self.verbose.info("%s grip subrepo %s CS changed to %s (which matches 'upstream')"%(repo_string, sr.get_name(), srw.git_repo_cs))
                    pass
                elif srw.git_repo_cs == srw.git_common_cs:
                    # Our CS is OLDER than upstream tip
                    self.verbose.info("%s grip subrepo %s wants to change to CS %s which is okay - but note 'upstream' is newer %s)"%(repo_string, sr.get_name(), srw.git_repo_cs, srw.git_upstream_cs))
                    pass
                else:
                    # Our CS is NEWER than upstream tip - requires subrepo push
                    self.verbose.message("%s grip subrepo %s wants to change to CS %s but 'upstream' is older %s)"%(repo_string, sr.get_name(), srw.git_repo_cs, srw.git_upstream_cs))
                    pass
                pass
            else:
                # Upstream config CS has changed from out last checkout
                pass
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
    #f update
    def update(self, force:bool=False, **kwargs:Any) -> bool:
        repo_string = self.get_repo_workflow_string()
        if self.grip_config_upstream_cs is None:
            self.verbose.info("%s has no upstream, so not updating"%(repo_string))
            return True
        reason = self.git_repo.rebase(other_branch=self.grip_config_upstream_cs)
        if reason is not None:
            raise WorkflowError("%s failed to update (%s)"%(repo_string, reason.get_reason()))
        return True
    #f commit
    def commit(self) -> bool:
        reason = self.git_repo.is_modified()
        if reason is not None:
            self.verbose.message("%s is modified (%s) - attempting a commit"%(self.get_repo_workflow_string(), reason.get_reason()))
            self.git_repo.commit()
            pass
        is_upstreamed = self.check_git_repo_is_upstreamed()
        if not is_upstreamed:
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
