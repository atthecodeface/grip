#a Imports
from .workflow import Workflow
from .workflow_readonly import *
from .workflow_single import *

#a Functions
def workflows():
    d = {}
    for w in Workflow.get_subclasses():
        d[w.name] = w
        pass
    return d
