from typing import Dict, Any, Optional, Callable, MutableMapping, Sequence, List, Tuple, Union
from typing_extensions import Protocol
class PrettyPrinter(Protocol):
    def __call__(self, __acc:Any, __s:str, indent:int=0)->Any: ...
    pass

DocumentationEntry = Union [ str, Tuple[str, List[Any] ] ]
Documentation = List[ DocumentationEntry ]
MakefileStrings = List[Tuple[str,str]]
EnvDict = Dict[str,str]
