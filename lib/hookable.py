from typing import Dict
class Hookable:
    """
    A class to which hooks may be added and where they may be invoked

    The hooks are a dictionary of <reason> : [ <hook_fn> ]

    A hook dictionary that has a key of cls.hook_key : hooks adds those
    hooks to the class hooks

    Invoking a list of hooks due to a reason
    """
    hooks : Dict = {}
    hook_key = None
    #f add_hooks
    @classmethod
    def add_hooks(cls, hooks):
        for (r,f) in hooks[cls.hook_key].items():
            if r not in cls.hooks:
                cls.hooks[r] = []
                pass
            cls.hooks[r] += f
            pass
        pass
    #f invoke_hooks
    def invoke_hooks(self, reason, **kwargs):
        if reason in self.hooks:
            for fn in self.hooks[hookname]:
                fn(self, **kwargs)
                pass
            pass
        pass

