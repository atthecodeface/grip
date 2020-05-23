#a Imports
from typing import Any
from .base import Workflow
from ..exceptions  import *
from ..git import branch_upstream

#a Classes
#c Readonly workflow
class ReadOnly(Workflow):
    """
    Read-only workflow for git repositories in a grip repo

    The git repository is not permitted to be modified;
    precommit hooks should be installed to indicate no modification is permitted
    no push is allowed
    """
    name = "readonly"
    #f install_hooks
    def install_hooks(self) -> None:
        raise Exception("install_hooks not implemented for %s"%self.name)
    #f status
    def status(self) -> bool:
        repo_string = self.get_repo_workflow_string()
        reason = self.git_repo.is_modified()
        if reason is not None:
            self.verbose.warning("%s is modified (%s), but the workflow for the repo is read-only."%(repo_string, reason.get_reason()))
            return True
        cmp = self.how_git_repo_upstreamed()
        if cmp==0:
            self.verbose.info("%s matches '%s' (%s)"%(repo_string, branch_upstream, self.git_repo_cs))
            pass
        elif cmp>0:
            self.verbose.message("%s is unmodified (%s) but a descendant of '%s' (%s) - maybe a 'fetch' is required?"%(repo_string, self.git_repo_cs, branch_upstream, self.git_upstream_cs))
            pass
        elif cmp==-1:
            self.verbose.message("%s is unmodified (%s) and an ancestor of '%s' (%s) - (if desired, 'git rebase %s' by hand in the repo brings it up to tip)"%(repo_string, self.git_repo_cs, branch_upstream, self.git_upstream_cs, branch_upstream))
            pass
        else:
            self.verbose.message("%s is at %s and '%s' is at %s - both have committed changes since last merge; if desired, 'git rebase %s' by hand in the repo brings it up to tip)"%(repo_string, self.git_repo_cs, branch_upstream, self.git_upstream_cs, branch_upstream))
            pass
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
        self.verbose.info("%s checking subrepos"%(repo_string))
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
                    self.verbose.info("%s grip subrepo %s CS changed to %s (which matches 'upstream' git branch)"%(repo_string, sr.get_name(), srw.git_repo_cs))
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
        self.verbose.info("%s subrepos checked"%(repo_string))
        reason = self.git_repo.is_modified()
        if reason is not None:
            self.verbose.warning("%s is modified (%s), but the workflow for the repo is read-only."%(repo_string, reason.get_reason()))
            return False
        return True
    #f update
    def update(self, **kwargs:Any) -> bool:
        repo_string = self.get_repo_workflow_string()
        self.get_git_repo_cs()
        if self.grip_config_upstream_cs==self.git_repo_cs:
            self.verbose.info("%s upstream is at grip config cs %s"%(repo_string, self.grip_config_upstream_cs))
            return True
        reason = self.git_repo.rebase(other_branch=self.grip_config_upstream_cs)
        self.verbose.info("%s rebase with cs %s to update to grip config"%(repo_string, self.grip_config_upstream_cs))
        if reason is not None:
            raise WorkflowError("%s failed to update (%s)"%(self.get_repo_workflow_string(), reason.get_reason()))
        return True
    #f update_as_grip
    def update_as_grip(self, **kwargs:Any) -> bool:
        """
        subrepos will be updated as required afterwards
        A read-only repo should not have any changed files; if its git_repo_cs does not match git_common_cs leave it up to the user
        """
        repo_string = self.get_repo_workflow_string()
        okay = True
        self.get_git_repo_cs()
        if self.git_repo_cs != self.git_common_cs:
            self.verbose.error("%s has been modified (at %s) since last update (%s) - must be sorted out by hand"%(repo_string, self.git_repo_cs, self.git_common_cs))
            return False
        if self.git_repo_cs == self.git_upstream_cs: # and upstream==common too, of course
            self.verbose.info("%s upstream has not changed"%(repo_string))
            return True
        reason = self.git_repo.rebase(other_branch=self.git_upstream_cs)
        if reason is not None:
            raise WorkflowError("%s failed to update (%s)"%(repo_string, reason.get_reason()))
        return True
    #f merge
    def merge(self, force:bool=False, **kwargs:Any) -> bool:
        if not force:
            self.verbose.warning("Skipping merge for readonly repo '%s'"%(self.git_repo.get_name()))
            return True
        r_cs = self.git_repo.get_cs()
        u_cs = self.git_repo.get_cs(branch_name=branch_upstream)
        if r_cs==u_cs: return True
        raise WorkflowError("Merge of read-only git repo '%s' should be done explicitly within that git repo."%(self.git_repo.get_name()))
    #f commit
    def commit(self) -> bool:
        repo_string = self.get_repo_workflow_string()
        reason = self.git_repo.is_modified()
        if reason is not None:
            raise WorkflowError("%s is modified (%s), but the workflow for the repo is read-only."%(self.get_repo_workflow_string(), reason.get_reason()))
        self.verbose.info("Readonly repo '%s' checked and is not modified"%(self.git_repo.get_name()))
        self.get_git_repo_cs()
        if self.git_repo_cs==self.grip_config_upstream_cs:
            self.verbose.info("%s matches upstream grip config"%(repo_string))
            return True
        is_upstreamed = self.check_git_repo_is_upstreamed()
        if not is_upstreamed:
            self.verbose.error("%s is at '%s' which is not upstreamed - it has probably been modified and committed locally, and if permitted then a git fetch, git rebase origin/master, git push, git branch %s origin/master may be what is needed."%(self.get_repo_workflow_string(), self.git_repo_cs, branch_upstream))
        return is_upstreamed
    #f prepush
    def prepush(self) -> bool:
        return True
    #f push
    def push(self) -> bool:
        return True
    #f All done
