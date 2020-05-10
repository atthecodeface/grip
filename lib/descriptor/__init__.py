from .stage  import Dependency as StageDependency
from .stage  import Descriptor as StageDescriptor
from .config import Descriptor as ConfigurationDescriptor
from .repo   import Descriptor as RepositoryDescriptor
from .repo   import DescriptorInConfig as RepositoryDescriptorInConfig
from .grip   import Descriptor as GripDescriptor

__all__ = ["StageDependency", "StageDescriptor", "ConfigurationDescriptor", "RepositoryDescriptor", "RepositoryDescriptorInConfig", "GripDescriptor"]

