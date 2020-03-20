#a Imports

#a Classes
#c Workflow - base class for workflows
class Workflow(object):
    name = "Base workflow class - must be subclassed"
    permitted = False
    #f install_hooks
    def install_hooks(self):
        """
        Install any hooks required in the subrepos?
        """
        raise Exception("install_hooks not implemented for workflow %s"%self.name)
    #f commit
    def commit(self, grip_repo, git_repo):
        """
        Commit a git_repo using the workflow

        Return True if completed, and False if not, or raise an exception if seriously cannot

        If True is returned then git_repo.get_cs() will return a CS that can be used for the grip state.
        """
        raise Exception("commit not implemented for workflow %s"%self.name)
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


