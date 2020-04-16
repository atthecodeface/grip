#a Imports
from .workflow import Workflow
from .exceptions  import *

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
    def prepush(self):
        return True
    def push(self):
        return True
    def commit(self):
        reason = self.git_repo.is_modified(log=self.log)
        if reason is not None:
            raise WorkflowError("Git repo '%s' is modified (%s), but the workflow for the repo is read-only."%(self.git_repo.get_name(), reason.get_reason()))
        self.verbose.verbose("Readonly repo '%s' checked and is not modified"%(self.git_repo.get_name()))
        # Would like to test that the CS is in the remote/branch, but that is not possible
        # We can check that it is in local branch upstream
        cs = self.git_repo.get_cs()
        cs_history = self.git_repo.get_cs_history(branch_name="upstream", log=self.log)
        if cs not in cs_history:
            raise WorkflowError("Readonly git repo '%s' is at cs '%s' but that is not a changeset that is in the 'upstream' branch; perhaps pulling the upstream branch from upstream remote would help? A readonly repo *must* be an ancestor of the remote branch head. If this repo really is a shiny new one to be pushed then do so, refresh the upstream branch locally, and retry the grip commit."%(self.git_repo.get_name(), cs))
        self.verbose.verbose("Readonly repo '%s' at cs %s - which is an ancestor of 'upstream' branch"%(self.git_repo.get_name(), cs))
        return True
