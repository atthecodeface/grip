#a Imports
from pathlib import Path

from ..exceptions  import *
from ..base        import GripBase
from ..descriptor  import RepositoryDescriptor
from ..descriptor  import RepositoryDescriptorInConfig
from ..descriptor  import ConfigurationDescriptor
from ..descriptor  import GripDescriptor
from ..configstate import ConfigFile as GripConfigFile
from ..configstate import StateFile  as GripStateFile
from ..configstate import StateFileConfig as GripStateFileConfig
from ..git         import Repository as GitRepository
from ..git         import Url as GitUrl
from ..repo        import Repository as GripRepository

from typing import ClassVar, List, Optional, Iterable, IO, Any
#a GripConfigState classes
#c GripConfigStateBase
class GripConfigStateBase(object):
    #v Base instance properties
    base              : GripBase
    grip_toml_path    : Path
    state_toml_path   : Path
    config_toml_path  : Path
    base_url          : GitUrl
    #v Properites of initial inherited by configured
    initial_repo_desc : GripDescriptor
    config_file       : GripConfigFile
    state_file        : GripStateFile
    config_desc       : ConfigurationDescriptor
    config_name : str
    state_file_config : GripStateFileConfig
    #f __init__
    def __init__(self, base:GripBase):
        self.base = base
        self.grip_toml_path   = self.base.grip_path(self.base.grip_toml_filename)
        self.state_toml_path  = self.base.grip_path(self.base.state_toml_filename)
        self.config_toml_path = self.base.grip_path(self.base.config_toml_filename)
        self.env_toml_path    = self.base.grip_path(self.base.env_toml_filename)
        self.base_url = self.base.get_git_repo().get_git_url()
        pass
    #f All done
    pass

#c GripConfigStateInitial
class GripConfigStateInitial(GripConfigStateBase):
    """
    An initial pass, getting initial_repo_desc, optional state_file, optional config_file
    """
    #v Properties private to Initial
    subrepo_descs     : List[RepositoryDescriptorInConfig]
    _has_state : bool
    _has_config_file : bool
    #f __init__
    def __init__(self, base:GripBase):
        GripConfigStateBase.__init__(self, base)
        self._has_state     = False
        self._has_config_file = False
        pass
    #f read_desc_initial - Read the inital grip.toml file without subrepos
    def read_desc_initial(self, error_handler:ErrorHandler=None) -> None:
        self.base.add_log_string("First pass reading '%s'"%str(self.grip_toml_path))
        self.initial_repo_desc = GripDescriptor(base=self.base)
        self.initial_repo_desc.read_toml_file(self.grip_toml_path, subrepo_descs=[])
        self.initial_repo_desc.read_environment(self.env_toml_path)
        self.initial_repo_desc.validate(check_stage_dependencies=False, error_handler=error_handler) # Don't check stage dependencies as they include subrepo files
        self.initial_repo_desc.resolve(config_name=None, error_handler=error_handler)
        self.initial_repo_desc.resolve_git_urls(self.base_url)
        if self.initial_repo_desc.is_logging_enabled():
            self.base.log.set_tidy(self.base.log_to_logfile)
            pass
        pass
    #f read_state - Read state.toml
    def read_state(self) -> None:
        self.base.add_log_string("Reading '%s'"%str(self.state_toml_path))
        self.state_file = GripStateFile(self.base)
        try:
            self.state_file.read_toml_file(self.state_toml_path)
            self._has_state = True
        except:
            raise
        pass
    #f read_config - Create GripConfig and read local.config.toml; set self.repo_config.config (GripConfig of config)
    def read_config(self) -> None:
        self.base.add_log_string("Reading local configuration state file '%s'"%str(self.config_toml_path))
        self.config_file = GripConfigFile(self.base)
        try:
            self.config_file.read_toml_file(self.config_toml_path)
            self._has_config_file = True
        except Exception as e:
            self._has_config_file = False
            self.base.add_log_string("Failed to read file: '%s'"%(str(e)))
            pass
        pass
    #f read_desc_state - Read grip.toml, state.toml
    def read_desc_state(self, error_handler:ErrorHandler=None) -> None:
        """
        Read the .grip/grip.toml grip description file, the
        .grip/state.toml grip state file, and any
        .grip/local.config.toml file.
        """
        self.read_desc_initial(error_handler=error_handler)
        self.read_state()
        self.read_config()
        pass
    #f has_config_file
    def has_config_file(self) -> bool:
        return self._has_config_file
    #f has_state
    def has_state(self) -> bool:
        return self._has_state
    #f select_configuration
    def select_configuration(self, config_name:Optional[str]) -> str:
        config_desc = self.initial_repo_desc.select_config(config_name)
        if config_desc is None:
            if config_name is None:
                raise UserError("Could not select default grip config - bad configuration")
            raise UserError("Could not select grip config '%s'; is it defined in the grip.toml file?"%config_name)
        self.config_desc = config_desc
        self.config_name = self.config_desc.name
        self.config_file.set_config_name(self.config_name)
        self.base.add_log_string("initial: select_configuration %s"%config_name)
        # state_file_config cannot be none if we use create_if_new - this fixes type checking
        state_file_config = self.state_file.select_config(self.config_name, create_if_new=True)
        assert state_file_config is not None
        self.state_file_config = state_file_config
        self.subrepo_descs = []
        for r in self.config_desc.iter_repos():
            self.subrepo_descs.append(r)
            pass
        return self.config_name
    #f select_current_configuration
    def select_current_configuration(self) -> None:
        assert self._has_config_file
        config_name = self.config_file.config
        self.select_configuration(config_name)
        pass
    #f iter_repos
    def iter_repos(self) -> Iterable[RepositoryDescriptorInConfig]:
        assert self.config_desc is not None
        for r in self.config_desc.iter_repos():
            yield r
            pass
        pass
    #f dump_to_file
    def dump_to_file(self, f:IO[str]) -> None:
        def p(acc:Any, s:str, indent:int=0) -> Any:
            print(("  "*indent)+s, file=f)
        self.initial_repo_desc.prettyprint("",p)
        pass
    #f All done
    pass

#c GripConfigStateConfigured
class GripConfigStateConfigured(GripConfigStateBase):
    """
    """
    clone_properties : ClassVar[List[str]] = ["initial_repo_desc",
                                              "config_file",
                                              "state_file",
                                              "config_desc",
                                              "config_name",
                                              "state_file_config"
    ]
    #v Instance properties
    full_repo_desc    : GripDescriptor
    subrepo_descs     : List[RepositoryDescriptorInConfig]
    #f __init__
    def __init__(self, initial:GripConfigStateInitial) -> None:
        GripConfigStateBase.__init__(self, initial.base)
        for k in self.clone_properties:
            setattr(self,k,getattr(initial,k))
            pass
        self.initial_subrepo_descs = initial.subrepo_descs
        pass
    #f read_desc - Create full_repo_desc by rereading grip.toml and those of subrepos
    def read_desc(self, error_handler:ErrorHandler=None) -> None:
        self.base.add_log_string("read_desc_configuration %s"%self.config_name)
        self.base.add_log_string("Second pass reading '%s' with %d subrepos"%(str(self.grip_toml_path),len(self.initial_subrepo_descs)))
        self.full_repo_desc = GripDescriptor(self.base)
        self.full_repo_desc.read_toml_file(self.grip_toml_path, subrepo_descs=self.initial_subrepo_descs, error_handler=error_handler)
        self.select_configuration(self.config_name)
        self.full_repo_desc.read_environment(self.env_toml_path)
        self.base.add_log_string("Validate full_repo_desc and selected configuration")
        self.base.add_log_string("Resolve full_repo_desc and selected configuration")
        self.full_repo_desc.resolve(config_name=self.config_name, error_handler=error_handler)
        self.full_repo_desc.resolve_git_urls(self.base_url)
        self.full_repo_desc.validate(check_stage_dependencies=True, error_handler=error_handler)
        if self.full_repo_desc.is_logging_enabled():
            self.base.log.set_tidy(self.base.log_to_logfile)
            pass
        pass
    #f select_configuration
    def select_configuration(self, config_name:Optional[str]) -> str:
        self.base.add_log_string("select_configuration %s"%config_name)
        config_desc = self.full_repo_desc.select_config(config_name)
        if config_desc is None:
            if config_name is None:
                raise UserError("Could not select default grip config - bad configuration")
            raise UserError("Could not select grip config '%s'; is it defined in the grip.toml file?"%config_name)
        self.config_desc = config_desc
        self.config_name = self.config_desc.name
        self.config_file.set_config_name(self.config_name)
        # state_file_config cannot be none if we use create_if_new - this fixes type checking
        state_file_config = self.state_file.select_config(self.config_name, create_if_new=True)
        assert state_file_config is not None
        self.state_file_config = state_file_config
        self.subrepo_descs = []
        for r in self.config_desc.iter_repos():
            self.subrepo_descs.append(r)
            pass
        return self.config_name
    #f iter_repos
    def iter_repos(self) -> Iterable[RepositoryDescriptorInConfig]:
        assert self.config_desc is not None
        for r in self.config_desc.iter_repos():
            yield r
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
        self.base.add_log_string("Writing state file '%s'"%str(self.state_toml_path))
        self.state_file.write_toml_file(self.state_toml_path)
        pass
    #f write_environment
    def write_environment(self) -> None:
        self.base.add_log_string("Writing environment file '%s'"%str(self.env_toml_path))
        self.full_repo_desc.write_environment(self.env_toml_path)
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
        self.base.add_log_string("Writing local configuration state file '%s'"%str(self.config_toml_path))
        self.config_file.write_toml_file(self.config_toml_path)
        pass

    #f dump_to_file
    def dump_to_file(self, f:IO[str]) -> None:
        def p(acc:Any, s:str, indent:int=0) -> Any:
            print(("  "*indent)+s, file=f)
        self.full_repo_desc.prettyprint("",p)
        pass
