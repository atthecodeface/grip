#a Imports
from typing import Type, List, Optional
from .base import Workflow
from .readonly import *
from .single import *

#a Functions
def supported_workflows() -> List[str]:
    d = []
    for w in Workflow.get_subclasses():
        d.append(w.name)
        pass
    return d

def get_workflow(name) -> Optional[Type[Workflow]]:
    for w in Workflow.get_subclasses():
        if w.name==name: return w
        pass
    return None

__all__ = ["Workflow", "get_workflow", "supported_workflows"]
