from typing import Dict, Callable, Any, Optional, List

T = Callable[..., Any]
HookDict = Dict[str, List[T]]
class Hookable:
    """
    A class to which hooks may be added and where they may be invoked

    The hooks are a dictionary of <reason> : [ <hook_fn> ]

    A hook dictionary that has a key of cls.hook_key : hooks adds those
    hooks to the class hooks

    Invoking a list of hooks due to a reason
    """
    hooks    : HookDict = {}
    hook_key : Optional[str] = None
    #f add_hooks
    @classmethod
    def add_hooks(cls, hooks:Dict[str, HookDict]) -> None:
        assert cls.hook_key is not None
        for (r,f) in hooks[cls.hook_key].items():
            if r not in cls.hooks:
                cls.hooks[r] = []
                pass
            cls.hooks[r] += f
            pass
        pass
    #f class_invoke_hooks
    @classmethod
    def class_invoke_hooks(self, hookname:str, **kwargs:Any) -> None:
        if hookname not in self.hooks: return
        for fn in self.hooks[hookname]:
            fn(self, **kwargs)
            pass
        pass
    #f invoke_hooks
    def invoke_hooks(self, hookname:str, **kwargs:Any) -> None:
        if hookname not in self.hooks: return
        for fn in self.hooks[hookname]:
            fn(self, **kwargs)
            pass
        pass

