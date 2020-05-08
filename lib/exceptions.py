from typing import Callable, Any, Optional

ErrorFn      = Callable[[Exception],Any]
# ErrorHandler = Optional[Callable[...,Any]]
ErrorHandler = Optional[ErrorFn]

class GripException(Exception):
    grip_type = "Undefined grip"
    def invoke(self, error_handler:ErrorHandler=None) -> Any:
        if error_handler is None: raise self
        return error_handler(self)
    @classmethod
    def error_handler(cls, f:ErrorFn, error_handler:ErrorHandler=None) -> ErrorFn:
        def handler(e:Exception) -> Any:
            if isinstance(e,cls):
                r=f(e)
                if r is not None: return r[0]
                pass
            if error_handler is None: raise e
            return error_handler(e)
        return handler
    pass

class InternalError(GripException):
    grip_type = "Internal grip"
    pass

class NotGripError(GripException):
    grip_type = "Not within a grip repository"
    pass

class PathError(GripException):
    grip_type = "Path error - e.g. file/directory does not exist"
    pass

class ConfigurationError(GripException):
    grip_type = "Grip repository configuration"
    pass

class UserError(GripException):
    """
    Cannot clone as directories already exist
    """
    grip_type = "User"
    pass

class WorkflowError(GripException):
    """
    """
    grip_type = "Workflow"
    pass

class SubrepoError(GripException):
    """
    """
    grip_type = "Subrepo"
    pass

#a Git reasons - exceptions for git
class GitReason(Exception):
    reason = "<unknown reason>"
    def get_reason(self) -> str:
        return self.reason
    def is_of(self, cls:Any) -> bool:
        return isinstance(self,cls)
    pass
class HowUnknownBranch(GitReason):
    reason = "unknown branch"
    pass
class HowUntrackedFiles(GitReason):
    reason = "untracked files"
    pass
class HowFilesModified(GitReason):
    reason = "modified files"
    pass

#a Exceptions
#c GripTomlError - exception used when reading the grip toml file
class GripTomlError(ConfigurationError):
    pass

#c RepoDescError - exception used when a repo description is invalid
class RepoDescError(ConfigurationError):
    pass

