#a Imports
from .workflow import Workflow

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
    def commit(self, grip_repo, git_repo):
        if git_repo.is_modified():
            raise Exception("Git repo '%s' is modified, but the workflow for the repo is read-only."%(git_repo.name))
        return True
    pass
