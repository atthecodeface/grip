#a Imports
import os, time
from pathlib import Path

from .verbose import Verbose
from .options import Options
from .log import Log
from .exceptions import *
from .base       import GripBase
from typing import Type, List, Dict, Iterable, Optional, Any, Tuple, cast
from .git import branch_upstream, branch_head
from .git import Repository as GitRepo
from .git import Url as GitUrl
from .descriptor import StageDependency as StageDependency
from .descriptor import RepositoryDescriptor
from .descriptor import ConfigurationDescriptor
from .descriptor import GripDescriptor as GripDescriptor
from .configstate import GripConfigStateInitial, GripConfigStateConfigured
from .repo import Repository, GripRepository

from .types import PrettyPrinter, Documentation, MakefileStrings, EnvDict

#a Classes
#a Toplevel grip repository class - this describes/contains the whole thing
#c Toplevel class
class Toplevel(GripBase):
    #v Instance properties
    invocation : str
    # repo_desc:   GripRepoDescriptor
    # repo_desc_config : Optional[ConfigurationDescriptor] - configured_config_state.config_desc
    # repo_config      : Optional[GripConfig]
    # grip_git_url : Optional[GitUrl]
    intial_config_state     : GripConfigStateInitial
    configured_config_state : GripConfigStateConfigured
    repo_instance_tree      : GripRepository
    _is_configured : bool
    #f find_git_repo_of_grip_root
    @classmethod
    def find_git_repo_of_grip_root(cls, path:Path, options:Options, log:Log) -> GitRepo:
        git_repo = GitRepo(path=path, permit_no_remote=True, options=options, log=log)
        path = git_repo.path()
        if not path.joinpath(Path(".grip")).is_dir():
            path = path.parent
            return cls.find_git_repo_of_grip_root(path, options=options, log=log)
        return git_repo
    #f clone - classmethod to perform a git clone and then create an instance
    @classmethod
    def clone(cls, repo_url:str, dest:Optional[Path], branch:Optional[str], options:Optional[Options]=None, log:Optional[Log]=None, invocation:str="")-> 'Toplevel':
        if options is None: options=Options()
        if log is None: log = Log()
        git_repo = GitRepo.clone(repo_url, new_branch_name="", branch=branch, dest=dest, options=options, log=log)
        return cls(path=git_repo.path(), git_repo=git_repo, options=options, log=log, invocation=invocation, ensure_configured=False)
    #f path - get a path relative to the repository
    def path(self, path:Optional[Path]=None) -> Path:
        return self.git_repo.path(path)
    #f __init__
    def __init__(self, options:Options, log:Log, path:Path, git_repo:Optional[GitRepo]=None, ensure_configured:bool=True, invocation:str="", error_handler:ErrorHandler=None):
        if git_repo is None:
            try:
                git_repo = Toplevel.find_git_repo_of_grip_root(path, options=options, log=log)
                pass
            except Exception as e:
                print(str(e))
                raise e
                pass
            pass
        if git_repo is None:
            raise NotGripError("Not within a git repository, so not within a grip repository either")
        GripBase.__init__(self, options=options, log=log, git_repo=git_repo, branch_name=None)
        self.invocation = time.strftime("%Y_%m_%d_%H_%M_%S") + ": " + invocation
        self.log.add_entry_string(self.invocation)
        self.initial_config_state = GripConfigStateInitial(self)
        self.initial_config_state.read_desc_state(error_handler=error_handler)
        self._is_configured = False
        if self.initial_config_state.has_config_file():
            self.initial_config_state.select_current_configuration()
            self.configured_config_state = GripConfigStateConfigured(self.initial_config_state)
            self.configured_config_state.read_desc(error_handler=error_handler)
            if options.get("debug_config",False):
                import sys
                self.configured_config_state.dump_to_file(sys.stdout)
            self._is_configured = True
            pass
        if ensure_configured and not self._is_configured:
            raise Exception("Die:ensure_configured and not self._is_configured:")
        self.make_branch_name()
        pass
    #f make_branch_name
    def make_branch_name(self) -> None:
        """
        Set branch name; if not configured, then generate a new name
        If configured then use the branch name in the local config state
        """
        if self.branch_name is None:
            if self.initial_config_state.config_file.branch is None:
                time_str = time.strftime("%Y_%m_%d_%H_%M_%S")
                base = self.initial_config_state.initial_repo_desc.get_name()
                if self.initial_config_state.config_file.config is not None:
                    base += "_" + self.initial_config_state.config_file.config
                    pass
                branch_name = "WIP__%s_%s"%(base, time_str)
                self.set_branch_name(branch_name)
                self.verbose.message("New branch name '%s'"%(branch_name))
                pass
            else:
                self.set_branch_name(self.initial_config_state.config_file.branch)
                pass
            pass
        pass
    #f update_state
    def update_state(self) -> None:
        self.configured_config_state.update_state(self.repo_instance_tree)
        pass
    #f write_state
    def write_state(self) -> None:
        self.configured_config_state.write_state()
        pass
    #f update_config
    def update_config(self) -> None:
        self.configured_config_state.update_config()
        pass
    #f write_config
    def write_config(self) -> None:
        self.configured_config_state.write_config()
        pass
    #f get_repo_desc
    def get_repo_desc(self) -> GripDescriptor:
        if self.is_configured():
            return self.configured_config_state.full_repo_desc
        return self.initial_config_state.initial_repo_desc
    #f debug_repo_desc
    def debug_repo_desc(self) -> str:
        def p(acc:str, s:str, indent:int=0) -> str:
            return acc+"\n"+("  "*indent)+s
        return cast(str,self.get_repo_desc().prettyprint("",p))
    #f get_name
    def get_name(self) -> str:
        return self.get_repo_desc().get_name()
    #f get_doc
    def get_doc(self) -> Documentation:
        """
        Return list of (name, documentation) strings
        If configured, list should include current configuration and repos
        If not configured, list should include all configurations
        List should always start with (None, repo.doc) if there is repo doc
        """
        if self.is_configured():
            return self.configured_config_state.config_desc.get_doc()
        return self.initial_config_state.initial_repo_desc.get_doc()
    #f get_configurations
    def get_configurations(self) -> List[str]:
        return self.get_repo_desc().get_configs()
    #f is_configured
    def is_configured(self) -> bool:
        return self._is_configured
    #f get_config_name
    def get_config_name(self) -> str:
        if self.is_configured():
            return self.configured_config_state.config_name
        raise Exception("Repo is not configured so has no config name")
    #f configure
    def configure(self, config_name:Optional[str]=None) -> None:
        force_configure = self.options.get("force_configure", default=False)
        self.add_log_string("Configuring repo %s with config %s"%(str(self.git_repo.path),config_name))
        if self.is_configured():
            if not force_configure:
                raise UserError("Grip repository is already configured - cannot configure it again, a new clone of the grip repo must be used instead")
            if (config_name is not None) and (config_name!=self.get_config_name()):
                raise UserError("Grip repository is already configured with config '%s' and cannot be configured with a different config name '%s'"%(self.get_config_name(),config_name))
            pass
        config_name = self.initial_config_state.select_configuration(config_name)
        assert config_name is not None
        self.configured_config_state = GripConfigStateConfigured(self.initial_config_state)
        self.add_log_string("...configuring toplevel for repo %s config %s"%(str(self.git_repo.path), config_name))
        self.configure_toplevel_repo()
        if not force_configure:
            self.check_clone_permitted()
            pass
        self.add_log_string("...cloning subrepos for repo %s"%(str(self.git_repo.path)))
        errors = self.clone_subrepos()
        if len(errors)>0:
            if not force_configure:
                for e in errors:
                    self.verbose.error("Error from cloning subrepo: %s"%e)
                    pass
                raise ConfigurationError("Failed to clone required subrepos")
            else:
                for e in errors:
                    self.verbose.warning("Failed to clone subrepo (but forcing configuration anyway): %s"%e)
                    pass
                pass
            pass                
        self.write_state()
        self.write_config()
        self.add_log_string("...rereading config and state for repo %s"%(str(self.git_repo.path)))
        self.configured_config_state.read_desc()
        self.add_log_string("...updating configuration for repo %s"%(str(self.git_repo.path)))
        self.create_subrepos()
        self._is_configured = True
        self.update_state()
        self.write_state()
        self.update_config()
        self.write_config()
        self.grip_env_write()
        self.create_grip_makefiles()
        pass
    #f configure_toplevel_repo - set toplevel git repo to have correct branches if it does not already
    def configure_toplevel_repo(self) -> None:
        """
        Must only be invoked if the grip repository is not yet configured
        In some circumstances the repository could have been git cloned by hand
        In this case we need to ensure it is unmodified, and set the required branches
        appropriately
        """
        assert self.branch_name is not None
        if self.git_repo.is_modified():
            raise ConfigurationError("Git repo is modified and cannot be configured")
        # The next bit is really for workflow single I think
        try:
            branch = self.git_repo.get_branch_name()
            pass
        except:
            raise ConfigurationError("Git repo is not at the head of a branch and so cannot be configured")
        has_upstream   = self.git_repo.has_cs(branch_name=branch_upstream)
        has_wip_branch = self.git_repo.has_cs(branch_name=self.branch_name)
        if has_upstream:
            remote = self.git_repo.get_branch_remote_and_merge(branch_upstream)
            pass
        else:
            remote = self.git_repo.get_branch_remote_and_merge(branch)
            pass
        if remote is None:
            raise ConfigurationError("Git repo branch does not have a remote to merge with and so cannot be configured")
        if has_upstream and has_wip_branch: return
        cs = self.git_repo.get_cs(branch_head)
        if not has_upstream:
            self.verbose.warning("Expected subrepo to already have upstream branch '%s'; will create one"%(branch_upstream))
            self.git_repo.change_branch_ref(branch_name=branch_upstream, ref=cs)
            pass
        if not has_wip_branch:
            self.verbose.message("Setting branches '%s' and '%s' to point at current head"%(branch_upstream, self.branch_name))
            self.git_repo.change_branch_ref(branch_name=self.branch_name, ref=cs)
            self.git_repo.checkout_cs(changeset=self.branch_name)
            pass
        self.git_repo.set_upstream_of_branch(branch_name=branch_upstream, remote=remote)
        pass
    #f reconfigure
    def reconfigure(self) -> None:
        if not self.is_configured():
            raise Exception("Grip repository is not properly configured - cannot reconfigure unless it has been")
        self.create_subrepos()

        for r in self.configured_config_state.config_desc.iter_repos():
            r_state = self.configured_config_state.state_file_config.get_repo_state(self.configured_config_state.config_desc, r.name)
        self.update_state()
        self.write_state()
        self.update_config()
        self.write_config()
        self.grip_env_write()
        self.create_grip_makefiles()
        pass
    #f check_clone_permitted
    def check_clone_permitted(self) -> None:
        for r in self.configured_config_state.config_desc.iter_repos():
            dest = self.git_repo.path(r.path())
            if not GitRepo.check_clone_permitted(r.url, branch=r.branch, dest=dest, log=self.log):
                raise UserError("Not permitted to clone '%s' to  '%s"%(r.url, dest))
            pass
        pass
    #f clone_subrepos - git clone the subrepos to the correct changesets
    def clone_subrepos(self, force_shallow:bool=False) -> List[str]:
        assert self.branch_name is not None
        errors = []
        # Clone all subrepos to the correct paths from url / branch at correct changeset
        # Use shallow if required
        for r in self.initial_config_state.iter_repos():
            # r : RepositoryDescriptor
            r_state = self.initial_config_state.state_file_config.get_repo_state(self.configured_config_state.config_desc, r.name)
            assert r_state is not None
            dest = self.git_repo.path(r.path())
            self.verbose.info("Cloning '%s' branch '%s' cs '%s' in to path '%s'"%(r.get_git_url_string(), r_state.branch, r_state.changeset, str(dest)))
            depth = None
            if r.is_shallow(): depth=1
            try:
                GitRepo.clone(repo_url=r.get_git_url_string(),
                              new_branch_name=self.branch_name,
                              branch=r_state.branch,
                              dest=dest,
                              depth = depth,
                              changeset = r_state.changeset,
                              options = self.options,
                              log = self.log )
                pass
            except Exception as e:
                errors.append(str(e))
                pass
            pass
        return errors
    #f create_subrepos - create python objects that correspond to the checked-out subrepos
    def create_subrepos(self) -> None:
        self.repo_instance_tree = GripRepository(name="<toplevel>", grip_repo=self, git_repo=self.git_repo, parent=None, workflow=self.configured_config_state.full_repo_desc.workflow )
        for rd in self.configured_config_state.config_desc.iter_repos():
            # rd : RepositoryDescriptor
            try:
                repo_path = self.git_repo.path(rd.path())
                gr = GitRepo(path=repo_path, options=self.options, log=self.log)
                sr = Repository(name=rd.name, grip_repo=self, parent=self.repo_instance_tree, git_repo=gr, workflow=rd.workflow)
                pass
            except SubrepoError as e:
                self.verbose.warning("Subrepo '%s' could not be found - is this grip repo a full checkout?"%(rd.name))
                pass
            pass
        self.repo_instance_tree.install_hooks()
        pass
    #f get_makefile_stamp_path
    def get_makefile_stamp_path(self, rd:StageDependency) -> Path:
        """
        Get an absolute path to a makefile stamp filename
        """
        rd_tgt = rd.target_name()
        rd_tgt_path = Path(self.grip_path(self.makefile_stamps_dirname)).joinpath(Path(rd_tgt))
        return rd_tgt_path
    #f create_grip_makefiles
    def create_grip_makefiles(self) -> None:
        """
        Repositories are all ready.
        Create makefile stamp directory
        Create makefile.env and makefile
        Delete makefile stamps
        """
        StageDependency.set_makefile_path_fn(self.get_makefile_stamp_path)
        self.add_log_string("Cleaning makefile stamps directory '%s'"%self.grip_path(self.makefile_stamps_dirname))
        makefile_stamps = self.grip_path(self.makefile_stamps_dirname)
        try:
            os.mkdir(makefile_stamps)
            pass
        except FileExistsError:
            pass
        self.add_log_string("Creating makefile environment file '%s'"%self.grip_path(self.grip_makefile_env_filename))
        with open(self.grip_path(self.grip_makefile_env_filename),"w") as f:
            print("GQ=@",file=f)
            print("GQE=@echo",file=f)
            for (n,v) in self.configured_config_state.config_desc.get_env_as_makefile_strings():
                print("%s=%s"%(n,v),file=f)
                pass
            for r in self.configured_config_state.config_desc.iter_repos():
                for (n,v) in r.get_env_as_makefile_strings():
                    print("# REPO %s wants %s=%s"%(r.name, n,v),file=f)
                    pass
                pass
            pass
        # create makefiles
        self.add_log_string("Creating makefile '%s'"%self.grip_path(self.grip_makefile_filename))
        with open(self.grip_path(self.grip_makefile_filename),"w") as f:
            print("THIS_MAKEFILE = %s\n"%(self.grip_path(self.grip_makefile_filename)), file=f)
            print("-include %s"%(self.grip_path(self.grip_makefile_env_filename)), file=f)
            def log_and_verbose(s:str) -> None:
                self.add_log_string(s)
                self.verbose.info(s)
                pass
            self.configured_config_state.config_desc.write_makefile_entries(f, verbose=log_and_verbose)
            pass
        # clean out make stamps
        pass
    #f get_root
    def get_root(self) -> Path:
        """
        Get path to grip repository
        """
        return self.git_repo.path()
    #f get_grip_env
    def get_grip_env(self) -> EnvDict:
        """
        Get immutable environment dictionary (not including OS environment)
        """
        return self.configured_config_state.config_desc.get_env()
    #f grip_env_iter
    def grip_env_iter(self) -> Iterable[Tuple[str,str]]:
        """
        Iterate through the grip env in alphabetically-sorted key order
        """
        d = self.get_grip_env()
        dk = list(d.keys())
        dk.sort()
        for k in dk:
            yield(k,d[k])
            pass
        pass
    #f grip_env_write
    def grip_env_write(self) -> None:
        """
        Write shell environment file
        """
        self.configured_config_state.write_environment()
        with open(self.grip_path(self.grip_env_filename), "w") as f:
            for (k,v) in self.grip_env_iter():
                print('%s="%s" ; export %s'%(k,v,k), file=f)
                pass
            pass
        pass
    #f invoke_shell - use created environment file to invoke a shell
    def invoke_shell(self, shell:str, args:List[str]=[]) -> None:
        env = {}
        for (k,v) in os.environ.items():
            env[k] = v
            pass
        env["GRIP_SHELL"] = shell
        cmd_line = ["grip_shell"]
        cmd_line += ["-c", "source %s; %s %s"%(self.grip_path(self.grip_env_filename), shell, " ".join(args))]
        os.execvpe("bash", cmd_line, env)
    #f status
    def status(self) -> None:
        self.create_subrepos()
        self.repo_instance_tree.status()
        pass
    #f commit
    def commit(self) -> None:
        self.create_subrepos()
        self.repo_instance_tree.commit()
        self.verbose.message("All repos commited")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f fetch
    def fetch(self) -> None:
        self.create_subrepos()
        self.repo_instance_tree.fetch()
        pass
    #f update
    def update(self) -> None:
        self.create_subrepos()
        self.repo_instance_tree.update()
        self.verbose.message("All subrepos updated")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        pass
    #f merge
    def merge(self) -> None:
        self.create_subrepos()
        self.repo_instance_tree.merge()
        self.verbose.message("All subrepos merged")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f publish
    def publish(self, prepush_only:bool=False) -> None:
        self.create_subrepos()
        self.repo_instance_tree.prepush()
        self.verbose.message("All subrepos prepushed")
        if prepush_only: return
        self.repo_instance_tree.push()
        self.verbose.message("All subrepos pushed")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f All done
