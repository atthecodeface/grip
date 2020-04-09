class GripException(Exception):
    grip_type = "Undefined grip"
    def invoke(self, error_handler=None):
        if error_handler is None: raise self
        return error_handler(self)
    @classmethod
    def error_handler(cls,f,error_handler=None):
        def handler(e):
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

