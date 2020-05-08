#a Imports
from ..exceptions  import *
from ..base        import GripBase
from ..descriptor  import RepositoryDescriptor
from ..descriptor  import ConfigurationDescriptor
from ..descriptor  import GripDescriptor
from ..configstate import ConfigFile as GripConfigFile
from ..configstate import StateFile  as GripStateFile
from ..configstate import StateFileConfig as GripStateFileConfig
from ..git         import Repository as GitRepository
from ..git         import Url as GitUrl
from ..repo        import Repository as GripRepository

from typing import ClassVar, List, Optional
#a GripConfigState classes
#c GripConfigStateBase
class GripConfigStateBase(object):
    #v Instance properties
    base              : GripBase
    grip_toml_filename   : str
    state_toml_filename  : str
    config_toml_filename : str
    base_url             : GitUrl
    initial_repo_desc : GripDescriptor
    config_file       : GripConfigFile
    state_file        : GripStateFile
    _has_state : bool
    _is_configured : bool
    clone_properties : ClassVar[List[str]] = ["base",
                                              "grip_toml_filename",
                                              "state_toml_filename",
                                              "config_toml_filename",
                                              "base_url",
                                              "initial_repo_desc",
                                              "config_file",
                                              "state_file",
                                              "_is_configured",
                                              "_has_state",
    ]
    #f __init__
    def __init__(self, base:GripBase):
        self.base = base
        self.grip_toml_filename   = self.base.grip_path(self.base.grip_toml_filename)
        self.state_toml_filename  = self.base.grip_path(self.base.state_toml_filename)
        self.config_toml_filename = self.base.grip_path(self.base.config_toml_filename)
        self.base_url = self.base.get_git_repo().get_git_url()
        self._has_state     = False
        self._is_configured = False
        pass
    #f clone - invoked instead of __init__ by subclasses if required
    def clone(self, clone:'GripConfigStateBase') -> None:
        for k in self.clone_properties:
            setattr(self,k,getattr(clone,k))
            pass
        pass
    #f read_desc_initial - Read the inital grip.toml file without subrepos
    def read_desc_initial(self) -> None:
        self.base.add_log_string("First pass reading '%s'"%self.grip_toml_filename)
        self.initial_repo_desc = GripDescriptor(git_repo=self.base.get_git_repo())
        self.initial_repo_desc.read_toml_file(self.grip_toml_filename, subrepo_descs=[])
        self.initial_repo_desc.resolve()
        self.initial_repo_desc.resolve_git_urls(self.base_url)
        if self.initial_repo_desc.is_logging_enabled():
            self.base.log.set_tidy(self.base.log_to_logfile)
            pass
        pass
    #f read_state - Read state.toml
    def read_state(self) -> None:
        self.base.add_log_string("Reading '%s'"%self.state_toml_filename)
        self.state_file = GripStateFile()
        try:
            self.state_file.read_toml_file(self.state_toml_filename)
            self._has_state = True
        except:
            raise
        pass
    #f read_config - Create GripConfig and read local.config.toml; set self.repo_config.config (GripConfig of config)
    def read_config(self) -> None:
        self.base.add_log_string("Reading local configuration state file '%s'"%self.config_toml_filename)
        self.config_file = GripConfigFile()
        try:
            self.config_file.read_toml_file(self.config_toml_filename)
            self._is_configured = True
        except Exception as e:
            self._is_configured = False
            self.base.add_log_string("Failed to read file: '%s'"%(str(e)))
            pass
        pass
    #f read_desc_state - Read grip.toml, state.toml
    def read_desc_state(self) -> None:
        """
        Read the .grip/grip.toml grip description file, the
        .grip/state.toml grip state file, and any
        .grip/local.config.toml file.
        """
        self.read_desc_initial()
        self.read_state()
        self.read_config()
        pass
    #f is_configured
    def is_configured(self) -> bool:
        return self._is_configured
    #f has_state
    def has_state(self) -> bool:
        return self._has_state
    #f All done
    pass

#c GripConfigStateInitial
class GripConfigStateInitial(GripConfigStateBase):
    """
    An initial pass, getting initial_repo_desc, optional state_file, optional config_file
    """
    config_name : str
    #f choose_configuration
    def choose_configuration(self, config_name:Optional[str]) -> str:
        config = self.initial_repo_desc.select_config(config_name)
        if config is None:
            if config_name is None:
                raise UserError("Could not select default grip config - bad configuration")
            raise UserError("Could not select grip config '%s'; is it defined in the grip.toml file?"%config_name)
        self.config_name = config.name
        self.config_file.set_config_name(self.config_name)
        return self.config_name
    pass

#c GripConfigStateUnconfigured
class GripConfigStateUnconfigured(GripConfigStateBase):
    #f __init__
    def __init__(self, initial:GripConfigStateInitial) -> None:
        GripConfigStateBase.clone(self, clone=initial)
        pass
    pass

#c GripConfigStateConfigured
class GripConfigStateConfigured(GripConfigStateBase):
    """
    """
    #v Instance properties
    config_name       : str
    state_file_config : GripStateFileConfig
    full_repo_desc    : GripDescriptor
    config_desc       : ConfigurationDescriptor
    subrepo_descs     : List[RepositoryDescriptor]
    #f __init__
    def __init__(self, initial:GripConfigStateInitial) -> None:
        GripConfigStateBase.clone(self, clone=initial)
        assert self.config_file.config is not None
        self.select_configuration(self.config_file.config)
        pass
    #f select_configuration - called by __init__ to turn this from GripConfigStateInitial to GripConfigStateConfigured
    def select_configuration(self, config_name:str) -> None:
        self.config_name = config_name
        config_desc = self.initial_repo_desc.select_config(config_name)
        if config_desc is None:
            raise ConfigurationError("Read local configuration file indicating grip configuration is '%s' but that is not in the repository description"%self.config_name)
        self.config_desc = config_desc
        # state_file_config cannot be none if we use create_if_new - this fixes type checking
        state_file_config = self.state_file.select_config(self.config_name, create_if_new=True)
        assert state_file_config is not None
        self.state_file_config = state_file_config
        self.subrepo_descs = []
        for r in self.config_desc.iter_repos():
            self.subrepo_descs.append(r)
            pass
        pass
    #f read_desc - Create full_repo_desc by rereading grip.toml and those of subrepos
    def read_desc(self, error_handler:ErrorHandler=None) -> None:
        self.base.add_log_string("Second pass reading '%s'"%self.grip_toml_filename)
        self.full_repo_desc = GripDescriptor(git_repo=self.base.get_git_repo())
        self.full_repo_desc.read_toml_file(self.grip_toml_filename, subrepo_descs=self.subrepo_descs, error_handler=error_handler)
        config_desc = self.full_repo_desc.select_config(self.config_name)
        if config_desc is None:
            raise ConfigurationError("Read local configuration file indicating grip configuration is '%s' but that is not in the repository description"%self.config_name)
        self.config_desc = config_desc
        self.full_repo_desc.validate(error_handler=error_handler)
        self.config_desc.validate()
        self.full_repo_desc.resolve(error_handler=error_handler)
        self.config_desc.resolve()
        self.full_repo_desc.resolve_git_urls(self.base_url)
        if self.full_repo_desc.is_logging_enabled():
            self.base.log.set_tidy(self.base.log_to_logfile)
            pass
        pass
    #f update_state
    def update_state(self, repo_tree:GripRepository) -> None:
        for r in repo_tree.iter_subrepos():
            self.state_file_config.update_repo_state(r.name, changeset=r.get_cs())
            pass
        pass
    #f write_state
    def write_state(self) -> None:
        self.base.add_log_string("Writing state file '%s'"%self.state_toml_filename)
        self.state_file.write_toml_file(self.state_toml_filename)
        pass
    #f update_config
    def update_config(self) -> None:
        git_url = self.base.get_git_repo().get_git_url()
        self.config_file.set_config_name(self.config_name)
        self.config_file.set_grip_git_url(git_url.as_string())
        self.config_file.set_branch_name(self.base.get_branch_name())
        pass
    #f write_config
    def write_config(self) -> None:
        self.base.add_log_string("Writing local configuration state file '%s'"%self.config_toml_filename)
        self.config_file.write_toml_file(self.config_toml_filename)
        pass
