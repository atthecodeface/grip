from typing import Dict, Any, Optional, Callable, MutableMapping, Sequence, List, Tuple, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing_extensions import Protocol
    class PrettyPrinter(Protocol):
        def __call__(self, __acc:Any, __s:str, indent:int=0)->Any: ...
        pass
    pass
else:
    class PrettyPrinter(object):
        pass
    pass

DocumentationHeadedContent = Tuple[str, List[Any] ] # where Any is DocumentationEntry really
DocumentationEntry = Union [ str, DocumentationHeadedContent ]
Documentation = List[ DocumentationEntry ]
MakefileStrings = List[Tuple[str,str]]
EnvDict = Dict[str,str]
