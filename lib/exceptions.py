class GripException(Exception):
    grip_type = "Undefined grip"
    pass

class InternalError(GripException):
    grip_type = "Internal grip"
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

