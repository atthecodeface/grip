#a Imports
import os, time
from typing import Type, List, Dict, Iterable, Optional
from .git import branch_upstream, branch_head
from .git import Repository as GitRepo
from .git import Url as GitUrl
from .log import Log
from .verbose import Verbose
from .options import Options
from .exceptions import *
from .descriptor import StageDependency as StageDependency
from .descriptor import GripDescriptor as GripRepoDescriptor
from .config.file import ConfigFile as GripRepoConfig
from .state.file import StateFile as GripRepoState
from .repo import Repository

#a Classes
#a GripRepository - subclass of Repository
class GripRepository(Repository):
    pass

#a Toplevel grip repository class - this describes/contains the whole thing
#c Toplevel class
class Toplevel:
    #v Static properties
    grip_dir_name = ".grip"
    grip_toml_filename   = "grip.toml"
    state_toml_filename  = "state.toml"
    config_toml_filename = "local.config.toml"
    grip_env_filename    = "local.env.sh"
    grip_log_filename    = "local.log"
    makefile_stamps_dirname = "local.makefile_stamps"
    grip_makefile_filename = "local.grip_makefile"
    grip_makefile_env_filename = "local.grip_makefile.env"
    #v Instance properties
    log : Log
    options : Options
    verbose : Verbose
    invocation : str
    git_repo : Optional[GitRepo]
    repo_config : Optional[GripRepoConfig]
    grip_git_url : Optional[GitUrl]
    #f find_git_repo_of_grip_root
    @classmethod
    def find_git_repo_of_grip_root(cls, path, options=None, log=None):
        git_repo = GitRepo(path, permit_no_remote=True, options=options, log=log)
        path = git_repo.get_path()
        if not os.path.isdir(os.path.join(path,".grip")):
            path = os.path.dirname(path)
            return cls.find_git_repo_of_grip_root(path, options=options, log=log)
        return git_repo
    #f clone - classmethod to create an instance after a git clone
    @classmethod
    def clone(cls, repo_url, branch, path=None, dest=None, options=None, log=None): # -> Type['Toplevel']
        if options is None: options=Options()
        if log is None: log = Log()
        dest_path = dest
        if path is not None:
            if dest_path is not None:
                dest_path = os.path.join(path,dest)
                pass
            else:
                dest_path = path
                pass
            pass
        repo = GitRepo.clone(repo_url, new_branch_name="WIP_GRIP", branch=branch, dest=dest_path, options=options, log=log)
        return cls(repo, options=options, log=log)
    #f __init__
    def __init__(self, git_repo:Optional[GitRepo]=None, path=None, options=None, log=None, ensure_configured=False, invocation="", error_handler=None):
        if options is None: options=Options()
        if log is None: log = Log()
        self.log=log
        self.options=options
        self.verbose=options.get_verbose_fn()
        self.invocation = time.strftime("%Y_%m_%d_%H_%M_%S") + ": " + invocation
        self.log.add_entry_string(self.invocation)
        if git_repo is None:
            try:
                git_repo = Toplevel.find_git_repo_of_grip_root(path, options=self.options, log=self.log)
            except Exception as e:
                print(str(e))
                raise e
                pass
            pass
        if git_repo is None:
            raise NotGripError("Not within a git repository, so not within a grip repository either")
        self.git_repo = git_repo
        self.repo_desc        = None
        self.repo_state       = None
        self.repo_config      = None
        self.repo_desc_config = None
        self.config_state     = None
        self.repo_instance_tree = None
        self.read_desc_state_config(use_current_config=True, error_handler=error_handler)
        assert self.repo_desc is not None
        if ensure_configured:
            if self.repo_desc_config is None:
                raise ConfigurationError("Unconfigured (or misconfigured) grip repository - has this grip repo been configured yet?")
            if self.config_state is None:
                raise ConfigurationError("Unconfigured (or misconfigured) grip repository - has this grip repo been configured yet?")
            pass
        self.grip_git_url = None
        if self.grip_git_url is None:      self.grip_git_url = git_repo.get_git_url()
        if self.grip_git_url is not None:
            self.repo_desc.resolve_git_urls(self.grip_git_url)
            pass
        pass
    #f log_to_logfile
    def log_to_logfile(self):
        """
        Invoked to append the log to the local logfile
        """
        with open(self.grip_path(self.grip_log_filename),"a") as f:
            print("",file=f)
            print("*"*80,file=f)
            self.log.dump(f)
            pass
        pass
    #f add_log_string
    def add_log_string(self, s):
        if self.log: self.log.add_entry_string(s)
        pass
    #f path
    def path(self, filenames=[]):
        return self.git_repo.filename(filenames)
    #f grip_path
    def grip_path(self, filename):
        return self.path([self.grip_dir_name, filename])
    #f grip_makefile_path
    def grip_makefile_path(self):
        return self.grip_path(self.grip_makefile_filename)
    #f set_branch_name
    def set_branch_name(self):
        """
        Set branch name; if not configured, then generate a new name
        If configured then use the branch name in the local config state
        """
        self.branch_name = None
        if self.repo_config is not None:
            self.branch_name = self.repo_config.branch
            pass
        if self.branch_name is None:
            time_str = time.strftime("%Y_%m_%d_%H_%M_%S")
            base = self.repo_desc.name
            if self.repo_config is not None and self.repo_config.config is not None: base+="_"+self.repo_config.config
            self.branch_name = "WIP__%s_%s"%(base, time_str)
            pass
        pass
    #f get_branch_name - get string branch name
    def get_branch_name(self, **kwargs:Any) -> str:
        """
        Get branch name
        """
        assert self.branch_name is not None
        return self.branch_name
    #f read_desc_state_config - Read grip.toml, state.toml, local.config.toml
    def read_desc_state_config(self, use_current_config=False, error_handler=None):
        """
        Read the .grip/grip.toml grip description file, the
        .grip/state.toml grip state file, and any
        .grip/local.config.toml file.

        If use_current_config is True then first read the grip description solely from .grip/grip.toml
        and then read the state and config.
        Then restart reading the .grip/grip.toml and any <subrepo>/grip.toml files as the grip description,
        then rebuild state and config
        """
        if use_current_config:
            self.read_desc_state_config(use_current_config=False, error_handler=error_handler)
            pass
        subrepos = [] # List of GitRepoDescs
        if use_current_config and (self.repo_desc_config is not None):
            for r in self.repo_desc_config.iter_repos():
                subrepos.append(r)
                pass
            pass
        self.read_desc(subrepos=subrepos, validate=use_current_config, error_handler=error_handler)
        self.read_state(error_handler=error_handler)
        self.read_config(error_handler=error_handler)
        pass
    #f read_desc - Create GripRepoDescriptor and read grip.toml (and those of subrepos)
    def read_desc(self, subrepos=[], validate=True, error_handler=None):
        """
        subrepos is a list of GitRepoDesc whose 'grip.toml' files should also be read if possible
        """
        self.add_log_string("Reading grip.toml file '%s'"%self.grip_path(self.grip_toml_filename))
        self.repo_desc = GripRepoDescriptor(git_repo=self.git_repo)
        self.repo_desc.read_toml_file(self.grip_path(self.grip_toml_filename), subrepos=subrepos, error_handler=error_handler)
        if validate:
            print("Validating and resolving")
            self.repo_desc.validate(error_handler=error_handler)
            self.repo_desc.resolve(error_handler=error_handler)
            if self.repo_desc.is_logging_enabled() and self.log:
                self.log.set_tidy(self.log_to_logfile)
                pass
            self.set_branch_name()
            pass
        else:
            print("Resolving")
            self.repo_desc.resolve(error_handler=error_handler)
            pass
        pass
    #f read_state - Read state.toml
    def read_state(self, error_handler=None):
        self.add_log_string("Reading state file '%s'"%self.grip_path(self.state_toml_filename))
        self.repo_state = GripRepoState()
        self.repo_state.read_toml_file(self.grip_path(self.state_toml_filename))
        pass
    #f read_config - Create GripRepoConfig and read local.config.toml; set self.repo_config.config (GripConfig of config)
    def read_config(self, error_handler=None):
        self.add_log_string("Reading local configuration state file '%s'"%self.grip_path(self.config_toml_filename))
        self.repo_desc_config = None
        self.config_state = None
        self.repo_config = GripRepoConfig()
        self.repo_config.read_toml_file(self.grip_path(self.config_toml_filename))
        if self.repo_config.config is not None:
            config_name = self.repo_config.config
            config = self.repo_desc.select_config(config_name)
            if config is None: raise ConfigurationError("Read config.toml indicating grip configuration is '%s' but that is not in the grip.toml description"%config_name)
            self.repo_desc_config = config
            self.config_state = self.repo_state.select_config(self.repo_desc_config.name)
            pass
        pass
    #f update_state
    def update_state(self):
        for r in self.repo_instance_tree.iter_subrepos():
            self.config_state.update_repo_state(r.name, changeset=r.get_cs())
            pass
        pass
    #f write_state
    def write_state(self):
        self.add_log_string("Writing state file '%s'"%self.grip_path(self.state_toml_filename))
        self.repo_state.write_toml_file(self.grip_path(self.state_toml_filename))
        pass
    #f update_config
    def update_config(self):
        self.repo_config.set_config_name(self.repo_desc_config.name)
        self.repo_config.set_grip_git_url(self.grip_git_url.as_string())
        self.repo_config.set_branch_name(self.branch_name)
        pass
    #f write_config
    def write_config(self):
        self.add_log_string("Writing local configuration state file '%s'"%self.grip_path(self.config_toml_filename))
        self.repo_config.write_toml_file(self.grip_path(self.config_toml_filename))
        pass
    #f debug_repodesc
    def debug_repodesc(self):
        def p(acc,s,indent=0):
            return acc+"\n"+("  "*indent)+s
        return self.repo_desc.prettyprint("",p)
    #f get_name
    def get_name(self):
        return self.repo_desc.name
    #f get_doc
    def get_doc(self):
        """
        Return list of (name, documentation) strings
        If configured, list should include current configuration and repos
        If not configured, list should include all configurations
        List should always start with (None, repo.doc) if there is repo doc
        """
        if self.is_configured():
            return self.repo_desc_config.get_doc()
        return self.repo_desc.get_doc()
    #f get_configurations
    def get_configurations(self):
        return self.repo_desc.get_configs()
    #f is_configured
    def is_configured(self):
        return self.repo_desc_config is not None
    #f get_config_name
    def get_config_name(self):
        if self.is_configured(): return self.repo_desc_config.get_name()
        raise Exception("Repo is not configured so has no config name")
    #f configure
    def configure(self, options, config_name=None):
        if self.repo_desc_config is not None:
            raise UserError("Grip repository is already configured - cannot configure it again, a new clone of the grip repo must be used instead")
        config = self.repo_desc.select_config(config_name)
        if config is None: raise UserError("Could not select grip config '%s'; is it defined in the grip.toml file?"%config_name)
        # print(config)
        self.repo_desc_config = config
        self.configure_toplevel_repo()
        self.check_clone_permitted()
        self.config_state = self.repo_state.select_config(self.repo_desc_config.name)
        self.clone_subrepos(options)
        self.update_state()
        self.write_state()
        self.update_config()
        self.write_config()
        self.grip_env_write()
        self.create_grip_makefiles()
        pass
    #f configure_toplevel_repo - set toplevel git repo to have correct branches if it does not already
    def configure_toplevel_repo(self):
        """
        Must only be invoked if the grip repository is not yet configured
        In some circumstances the repository could have been git cloned by hand
        In this case we need to ensure it is unmodified, and set the required branches
        appropriately
        """
        if self.git_repo.is_modified():
            raise ConfigurationError("Git repo is modified and cannot be configured")
        # The next bit is really for workflow single I think
        try:
            branch = self.git_repo.get_branch_name(log=self.log)
            pass
        except:
            raise ConfigurationError("Git repo is not at the head of a branch and so cannot be configured")
        (origin, push_branch) = self.git_repo.get_branch_remote_and_merge(branch)
        if (origin is None) or (push_branch is None):
            raise ConfigurationError("Git repo branch does not have a remote to merge with and so cannot be configured")
        has_upstream   = self.git_repo.has_cs(branch_name=branch_upstream, log=self.log)
        has_wip_branch = self.git_repo.has_cs(branch_name=self.branch_name, log=self.log)
        if has_upstream and has_wip_branch: return
        if has_upstream:
            raise Exception("Grip repository git repo has branch '%s' but not the WIP branch '%s' - try a proper clone"%(branch_upstream, self.branch_name))
        if has_wip_branch:
            raise Exception("Grip repository git repo does not have branch '%s' but *has* not the WIP branch '%s' - try a proper clone"%(branch_upstream, self.branch_name))
        cs = self.git_repo.get_cs(branch_head)
        self.verbose.message("Setting branches '%s' and '%s' to point at current head"%(branch_upstream, self.branch_name))
        self.git_repo.change_branch_ref(branch_name=branch_upstream, ref=cs, log=self.log)
        self.git_repo.change_branch_ref(branch_name=self.branch_name, ref=cs, log=self.log)
        self.git_repo.set_upstream_of_branch(branch_name=branch_upstream, origin=origin, origin_branch=push_branch, log=self.log)
        pass
    #f reconfigure
    def reconfigure(self, options):
        if self.repo_desc_config is None:
            raise Exception("Grip repository is not properly configured - cannot reconfigure unless it has been")
        self.create_subrepos()
        for r in self.repo_desc_config.iter_repos():
            r_state = self.config_state.get_repo_state(self.repo_desc_config, r.name)
        self.update_state()
        self.write_state()
        self.update_config()
        self.write_config()
        self.grip_env_write()
        self.create_grip_makefiles()
        pass
    #f check_clone_permitted
    def check_clone_permitted(self):
        for r in self.repo_desc_config.iter_repos():
            dest = self.git_repo.filename([r.path])
            if not GitRepo.check_clone_permitted(r.url, branch=r.branch, dest=dest, log=self.log):
                raise UserError("Not permitted to clone '%s' to  '%s"%(r.url, dest))
            pass
        pass
    #f clone_subrepos - git clone the subrepos to the correct changesets
    def clone_subrepos(self, options, force_shallow=False):
        # Clone all subrepos to the correct paths from url / branch at correct changeset
        # Use shallow if required
        for r in self.repo_desc_config.iter_repos():
            r_state = self.config_state.get_repo_state(self.repo_desc_config, r.name)
            dest = self.git_repo.filename([r.path])
            self.verbose.info("Cloning '%s' branch '%s' cs '%s' in to path '%s'"%(r.get_git_url_string(), r_state.branch, r_state.changeset, dest))
            depth = None
            if r.is_shallow(): depth=1
            r.git_repo = GitRepo.clone(repo_url=r.get_git_url_string(),
                                       new_branch_name=self.branch_name,
                                       branch=r_state.branch,
                                       dest=dest,
                                       depth = depth,
                                       changeset = r_state.changeset,
                                       options = self.options,
                                       log = self.log )
            pass
        self.create_subrepos()
        pass
    #f create_subrepos - create python objects that correspond to the checked-out subrepos
    def create_subrepos(self):
        self.repo_instance_tree = Repository(name="<toplevel>", grip_repo=self, git_repo=self.git_repo, parent=None, repo_desc=self.repo_desc )
        for rd in self.repo_desc_config.iter_repos():
            try:
                gr = GitRepo(path_str=self.git_repo.filename([rd.path]), options=self.options, log=self.log)
                sr = Repository(name=rd.name, grip_repo=self, parent=self.repo_instance_tree, git_repo=gr, repo_desc=rd)
                pass
            except SubrepoError as e:
                self.verbose.warning("Subrepo '%s' could not be found - is this grip repo a full checkout?"%(r.name))
                pass
            pass
        self.repo_instance_tree.install_hooks()
        pass
    #f get_makefile_stamp_path
    def get_makefile_stamp_path(self, rd):
        """
        Get an absolute path to a makefile stamp filename
        """
        rd_tgt = rd.target_name()
        return os.path.join(self.grip_path(self.makefile_stamps_dirname), rd_tgt)
    #f create_grip_makefiles
    def create_grip_makefiles(self):
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
            for (n,v) in self.repo_desc_config.get_env_as_makefile_strings():
                print("%s=%s"%(n,v),file=f)
                pass
            for r in self.repo_desc_config.iter_repos():
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
            def log_and_verbose(s):
                self.add_log_string(s)
                self.verbose.info(s)
                pass
            self.repo_desc_config.write_makefile_entries(f, verbose=log_and_verbose)
            pass
        # clean out make stamps
        pass
    #f get_root
    def get_root(self):
        """
        Get absolute path to grip repository
        """
        return self.git_repo.get_path()
    #f get_grip_env
    def get_grip_env(self):
        """
        Get immutable environment dictionary (not including OS environment)
        """
        return self.repo_desc_config.get_env()
    #f grip_env_iter
    def grip_env_iter(self):
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
    def grip_env_write(self):
        """
        Write shell environment file
        """
        with open(self.grip_path(self.grip_env_filename), "w") as f:
            for (k,v) in self.grip_env_iter():
                print('%s="%s" ; export %s'%(k,v,k), file=f)
                pass
            pass
        pass
    #f invoke_shell - use created environment file to invoke a shell
    def invoke_shell(self, shell, args=None):
        env = {}
        for (k,v) in os.environ.items():
            env[k] = v
            pass
        env["GRIP_SHELL"] = shell
        cmd_line = ["grip_shell"]
        cmd_line += ["-c", "source %s; %s %s"%(self.grip_path(self.grip_env_filename), shell, " ".join(args))]
        os.execvpe("bash", cmd_line, env)
    #f status
    def status(self):
        self.create_subrepos()
        self.repo_instance_tree.status()
        pass
    #f commit
    def commit(self):
        self.create_subrepos()
        self.repo_instance_tree.commit()
        self.verbose.message("All repos commited")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f fetch
    def fetch(self):
        self.create_subrepos()
        self.repo_instance_tree.fetch()
        pass
    #f merge
    def merge(self):
        self.create_subrepos()
        self.repo_instance_tree.merge()
        self.verbose.message("All subrepos merged")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f publish
    def publish(self, prepush_only=False):
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
