#a Imports
from .workflow import Workflow
from .exceptions  import *
from .git import branch_upstream

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
    def install_hooks(self):
        raise Exception("install_hooks not implemented for %s"%self.name)
    def status(self):
        repo_string = self.get_repo_workflow_string()
        reason = self.git_repo.is_modified(options=None, log=self.log)
        if reason is not None:
            self.verbose.warning("%s is modified (%s), but the workflow for the repo is read-only."%(repo_string, reason.get_reason()))
            return
        (cs, cs_upstream, cmp) = self.how_git_repo_upstreamed()
        if cmp==0:
            self.verbose.info("%s matches '%s' (%s)"%(repo_string, branch_upstream, cs))
            pass
        elif cmp>0:
            self.verbose.message("%s is unmodified (%s) but a descendant of '%s' (%s) - maybe a 'fetch' is required?"%(repo_string, cs, branch_upstream, cs_upstream))
            pass
        else:
            self.verbose.message("%s is unmodified (%s) and an ancestor of '%s' (%s) - (if desired, 'git rebase %s' by hand in the repo brings it up to tip)"%(repo_string, cs, branch_upstream, cs_upstream, branch_upstream))
            pass
        return
    def merge(self, force=False):
        if not force:
            self.verbose.warning("Skipping merge for readonly repo '%s'"%(self.git_repo.get_name()))
            return True
        r_cs = self.git_repo.get_cs(log=self.log)
        u_cs = self.git_repo.get_cs(branch_name=branch_upstream, log=self.log)
        if r_cs==u_cs: return True
        raise WorkflowError("Merge of read-only git repo '%s' should be done explicitly within that git repo."%(self.git_repo.get_name()))
    def prepush(self):
        return True
    def push(self):
        return True
    def commit(self):
        reason = self.git_repo.is_modified(options=None, log=self.log)
        if reason is not None:
            raise WorkflowError("%s is modified (%s), but the workflow for the repo is read-only."%(self.get_repo_workflow_string(), reason.get_reason()))
        self.verbose.info("Readonly repo '%s' checked and is not modified"%(self.git_repo.get_name()))
        r_cs = self.git_repo.get_cs(log=self.log)
        is_upstreamed = self.check_git_repo_is_upstreamed()
        self.verbose.error("%s is at '%s' which is not upstreamed - it has probably been modified and committed locally, and if permitted then a git fetch, git rebase origin/master, git push, git branch %s origin/master may be what is needed."%(self.get_repo_workflow_string(), r_cs, branch_upstream))
        return is_upstreamed
