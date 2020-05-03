#a Imports
from .git import *

#a Classes
#c Workflow - base class for workflows
class Workflow(object):
    name = "Base workflow class - must be subclassed"
    permitted = False
    #f __init__
    def __init__(self, grip_repo, git_repo, log, verbose):
        self.grip_repo = grip_repo
        self.git_repo = git_repo
        self.options = self.grip_repo.options
        self.log = log
        self.verbose = verbose
        pass
    #f install_hooks
    def install_hooks(self):
        """
        Install any hooks required in the subrepos?
        """
        raise Exception("install_hooks not implemented for workflow %s"%self.name)
    #f get_repo_workflow_string
    def get_repo_workflow_string(self):
        return "Repo (%s) %s"%(self.name, self.git_repo.get_name())
    #f status
    def status(self):
        """
        Report status of a git repo given a workflow
        """
        raise Exception("status not implemented for workflow %s"%self.name)
    #f commit
    def commit(self):
        """
        Commit a git_repo using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("commit not implemented for workflow %s"%self.name)
    #f fetch
    def fetch(self):
        self.verbose.info("Fetching %s"%(self.get_repo_workflow_string()))
        output = self.git_repo.fetch(log=self.log)
        if len(output)>0:print(output)
        current_cs = self.git_repo.get_cs(branch_name="upstream")
        fetched_cs = self.git_repo.get_cs(branch_name="upstream@{upstream}")
        self.git_repo.change_branch_ref(log=self.log, branch_name="upstream", ref=fetched_cs)
        self.verbose.message("Upstream branch of repo '%s' now at %s (was at %s)"%(self.git_repo.get_name(), fetched_cs, current_cs))
        return True
    #f merge
    def merge(self):
        """
        Merge a git_repo with upstream using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("merge not implemented for workflow %s"%self.name)
    #f prepush
    def prepush(self):
        """
        Prepare to push a git_repo upstream using the workflow
        This may be a merge; it may be nothing

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("prepush not implemented for workflow %s"%self.name)
    #f push
    def push(self):
        """
        Push a git_repo upstream using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("push not implemented for workflow %s"%self.name)
    #f check_git_repo_is_descendant
    def check_git_repo_is_descendant(self):
        cs_history = self.git_repo.get_cs_history(branch_name=self.grip_repo.branch_name, log=self.log)
        try:
            cs = self.git_repo.get_cs(branch_name="upstream")
        except HowUnknownBranch as e:
            raise WorkflowError("%s"%str(e))
        if cs not in cs_history:
            raise WorkflowError("%s is not a descendant of upstream which is at cs '%s' - have they been merged?"%(self.get_repo_workflow_string(), cs))
        self.verbose.info("%s is a descendant of 'upstream' branch (at cs %s)"%(self.get_repo_workflow_string(), cs))
        return True
    #f how_git_repo_upstreamed
    def how_git_repo_upstreamed(self):
        """
        Return 0 if git repo matches upstream
        Return 1 if git repo is descendant of upstream
        Return -1 if git repo is ancestor of upstream
        """
        cs = self.git_repo.get_cs(log=self.log)
        cs_upstream = self.git_repo.get_cs(branch_name="upstream", log=self.log)
        if cs==cs_upstream: return (cs, cs_upstream, 0)
        try:
            cs_history = self.git_repo.get_cs_history(branch_name="upstream", log=self.log)
        except HowUnknownBranch as e:
            raise WorkflowError("%s"%str(e))
        if cs in cs_history: return (cs, cs_upstream, -1)
        return (cs, cs_upstream, 1)
    #f check_git_repo_is_upstreamed
    def check_git_repo_is_upstreamed(self):
        (cs, cs_upstream, cmp) = self.how_git_repo_upstreamed()
        if cmp>0:
            raise WorkflowError("%s is at cs '%s' but that is not a changeset that is in the 'upstream' branch; perhaps pulling the upstream branch from upstream remote would help? The *must* be an ancestor of the remote branch head. If this repo really is a shiny new one to be pushed then do so, refresh the upstream branch locally, and retry the grip commit."%(self.get_repo_workflow_string(), cs))
        self.verbose.info("%s is at cs %s - which is an ancestor of 'upstream' branch"%(self.get_repo_workflow_string(), cs))
        return True
    #f get_subclasses
    @classmethod
    def get_subclasses(cls, so_far=set()):
        for subclass in cls.__subclasses__():
            if subclass not in so_far:
                so_far.add(subclass)
                yield subclass
                subclass.get_subclasses(so_far)
                pass
            pass
        pass


