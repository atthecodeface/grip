#a Imports
import os, time
from .git import GitRepo
from .repodesc import GripRepoDesc
from .repostate import GripRepoState
from .repoconfig import GripRepoConfig
from .workflows import workflows
from .log import Log
from .verbose import Verbose
from .exceptions import *

def pp_stdout(acc, s, indent=0):
    print("  "*indent+acc+s)
    return ""

#a Classes
#c GripSubrepo class
class GripSubrepo:
    ws = workflows()
    #f __init__
    def __init__(self, grip_repo, repo_desc):
        self.name = repo_desc.name
        self.grip_repo = grip_repo
        self.git_repo = GitRepo(path=grip_repo.git_repo.filename([repo_desc.path]))
        self.workflow = repo_desc.workflow(grip_repo, self.git_repo, grip_repo.log, grip_repo.verbose)
        pass
    #f install_hooks
    def install_hooks(self):
        pass
    #f status
    def status(self):
        try:
            s = "Getting status of repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            # self.grip_repo.verbose.info(s)
            self.workflow.status()
            pass
        except Exception as e:
            raise(e)
        pass
    #f commit
    def commit(self):
        try:
            s = "Commiting repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.message(s)
            okay = self.workflow.commit()
            if not okay: raise(Exception("Commit for repo '%s' not permitted"%self.name))
            cs = self.get_cs()
            self.grip_repo.add_log_string("Repo '%s' at commit hash '%s'"%(self.name, cs))
            pass
        except Exception as e:
            raise(e)
        pass
    #f fetch
    def fetch(self):
        try:
            s = "Fetching repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.fetch()
            if not okay: raise(Exception("Fetch for repo '%s' not permitted"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f merge
    def merge(self, force=False):
        try:
            s = "Merging repo '%s' with workflow '%s' (force %s)"%(self.name, self.workflow.name, str(force))
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.merge(force=force)
            if not okay: raise(Exception("Merge for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f prepush
    def prepush(self):
        try:
            s = "Prepushing repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.prepush()
            if not okay: raise(Exception("Prepush for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f push
    def push(self):
        try:
            s = "Pushing repo '%s' with workflow '%s'"%(self.name, self.workflow.name)
            self.grip_repo.add_log_string(s)
            self.grip_repo.verbose.info(s)
            okay = self.workflow.push()
            if not okay: raise(Exception("Push for repo '%s' failed"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    #f get_cs
    def get_cs(self):
        return self.git_repo.get_cs()
    #f All done
    pass

#c GripRepo class
class GripRepo:
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
    #f find_git_repo_of_grip_root
    @staticmethod
    def find_git_repo_of_grip_root(path, log=None):
        git_repo = GitRepo(path, permit_no_remote=True, log=log)
        path = git_repo.get_path()
        if not os.path.isdir(os.path.join(path,".grip")):
            path = os.path.dirname(path)
            return GripRepo.find_git_repo_of_grip_root(path, log=log)
        return git_repo
    #f __init__
    def __init__(self, git_repo=None, path=None, options=None, ensure_configured=False, invocation="", error_handler=None):
        self.log=Log()
        self.options=options
        self.verbose=options.verbose
        self.invocation = time.strftime("%Y_%m_%d_%H_%M_%S") + ": " + invocation
        self.log.add_entry_string(self.invocation)
        if git_repo is None:
            git_repo = GripRepo.find_git_repo_of_grip_root(path, self.log)
            pass
        if git_repo is None:
            raise Exception("Not within a git repository, so not within a grip repository either")
        self.git_repo = git_repo
        self.repo_desc        = None
        self.repo_state       = None
        self.repo_config      = None
        self.repo_desc_config = None
        self.config_state     = None
        self.subrepos         = None
        self.read_desc_state_config(use_current_config=True, error_handler=error_handler)
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
    #f read_desc_state_config
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
        subrepos = []
        if use_current_config and (self.repo_desc_config is not None):
            for r in self.repo_desc_config.iter_repos():
                subrepos.append(r)
                pass
            pass
        self.read_desc(subrepos=subrepos, error_handler=error_handler)
        self.read_state(error_handler=error_handler)
        self.read_config(error_handler=error_handler)
        pass
    #f read_desc
    def read_desc(self, subrepos=[], error_handler=None):
        self.add_log_string("Reading grip.toml file '%s'"%self.grip_path(self.grip_toml_filename))
        self.repo_desc = GripRepoDesc(git_repo=self.git_repo)
        self.repo_desc.read_toml_file(self.grip_path(self.grip_toml_filename), subrepos=subrepos, error_handler=error_handler)
        if self.repo_desc.is_logging_enabled() and self.log:
            self.log.set_tidy(self.log_to_logfile)
            pass
        self.set_branch_name()
        pass
    #f read_state
    def read_state(self, error_handler=None):
        self.add_log_string("Reading state file '%s'"%self.grip_path(self.state_toml_filename))
        self.repo_state = GripRepoState()
        self.repo_state.read_toml_file(self.grip_path(self.state_toml_filename))
        pass
    #f read_config
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
        for r in self.subrepos:
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
        self.repo_config.config       = self.repo_desc_config.name
        self.repo_config.grip_git_url = self.grip_git_url.git_url()
        self.repo_config.branch       = self.branch_name
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
    #f clone_subrepos
    def clone_subrepos(self, options, force_shallow=False):
        # Clone all subrepos to the correct paths from url / branch at correct changeset
        # Use shallow if required
        # git clone --depth 1 --single-branch --branch <name> --no-checkout
        # git checkout --detach <changeset>
        for r in self.repo_desc_config.iter_repos():
            r_state = self.config_state.get_repo_state(self.repo_desc_config, r.name)
            dest = self.git_repo.filename([r.path])
            self.verbose.info("Cloning '%s' branch '%s' cs '%s' in to path '%s'"%(r.get_git_url_string(), r_state.branch, r_state.changeset, dest))
            depth = None
            if r.is_shallow(): depth=1
            r.git_repo = GitRepo.clone(options,
                                       repo_url=r.get_git_url_string(),
                                       new_branch_name=self.branch_name,
                                       branch=r_state.branch,
                                       dest=dest,
                                       depth = depth,
                                       changeset = r_state.changeset )
            pass
        self.create_subrepos()
        for r in self.subrepos:
            r.install_hooks()
            pass
        pass
    #f create_subrepos
    def create_subrepos(self):
        self.subrepos = []
        for r in self.repo_desc_config.iter_repos():
            self.subrepos.append(GripSubrepo(self, r))
            pass
        pass
    #f xupdate_subrepos
    def xupdate_subrepos(self):
        # Maybe not do this at all for now?
        pass
    #f xupdate_grip_env
    def xupdate_grip_env(self):
        # repos are up-to-date
        # recreate environment
        # clean out make stamps
        pass
    #f get_makefile_stamp_filename
    def get_makefile_stamp_filename(self, rd):
        """
        Get an absolute path to a makefile stamp filename
        """
        rd_tgt = rd.target_name()
        return os.path.join(self.grip_path(self.makefile_stamps_dirname), rd_tgt)
    #f get_makefile_stamp
    def get_makefile_stamp(self, rd):
        """
        Get makefile stamp of a 'stage', 'requires' or 'satisfies'
        """
        return rd.target_name()
    #f new_makefile_stamp
    def new_makefile_stamp(self,rd):
        """
        Get an absolute path to a makefile stamp filename
        Clean the file if it exists

        If repo is None then it is a global stage
        """
        rd_tgt = self.get_makefile_stamp(rd)
        rd_tgt_filename = self.get_makefile_stamp_filename(rd)
        if os.path.exists(rd_tgt_filename): os.unlink(rd_tgt_filename)
        return (rd_tgt, rd_tgt_filename)
    #f create_grip_makefiles
    def create_grip_makefiles(self):
        """
        Repositories are all ready.
        Create makefile stamp directory
        Create makefile.env and makefile
        Delete makefile stamps
        """
        self.add_log_string("Cleaning makefile stamps directory '%s'"%self.grip_path(self.makefile_stamps_dirname))
        makefile_stamps = self.grip_path(self.makefile_stamps_dirname)
        try:
            os.mkdir(makefile_stamps)
            pass
        except FileExistsError:
            pass
        self.add_log_string("Creating makefile environment file '%s'"%self.grip_path(self.grip_makefile_env_filename))
        with open(self.grip_path(self.grip_makefile_env_filename),"w") as f:
            for (n,v) in self.repo_desc_config.get_env_as_makefile_strings():
                print("%s:=%s"%(n,v),file=f)
                pass
            for r in self.repo_desc_config.iter_repos():
                for (n,v) in r.get_env_as_makefile_strings():
                    print("%s:=%s"%(n,v),file=f)
                    pass
                pass
            pass
        # create makefiles
        self.add_log_string("Creating makefile '%s'"%self.grip_path(self.grip_makefile_filename))
        with open(self.grip_path(self.grip_makefile_filename),"w") as f:
            print("-include %s"%(self.grip_path(self.grip_makefile_env_filename)), file=f)
            stages = self.repo_desc_config.get_global_stages()
            for (sn,s) in stages.items():
                self.add_log_string("Adding global stage '%s'"%sn)
                (stgt, stgt_filename) = self.new_makefile_stamp(s)
                print("\n.PHONY: %s revoke.%s"%(stgt, stgt), file=f)
                print("%s: %s"%(stgt, stgt_filename), file=f)
                print("revoke.%s:\n\trm -f %s"%(stgt, stgt_filename), file=f)
                pass
            def write_to_makefile(acc, repo, stage):
                (rstgt, rstgt_filename) = self.new_makefile_stamp(stage.dependency)
                self.add_log_string("Adding target '%s'"%rstgt)
                wd = stage.wd
                if wd is None: wd = self.git_repo.filename(repo.path)
                env = ""
                for (k,v) in stage.env.as_makefile_strings():
                    env = env + (" %s=%s"%(k,v))
                    pass
                if env != "": env = env + ";"
                exec = stage.exec
                if exec is None: exec=""
                print("\nGRIP_%s_%s_ENV := %s"%(repo.name, stage.name, env), file=f)
                print("\n.PHONY: %s revoke.%s"%(rstgt, rstgt), file=f)
                print("%s: %s"%(rstgt, rstgt_filename), file=f)
                print("revoke.%s:\n\trm -f %s"%(rstgt, rstgt_filename), file=f)
                print("%s:"%(rstgt_filename), file=f)
                print("\t$(GRIP_%s_%s_ENV) cd %s && (%s)"%(repo.name, stage.name, wd, exec), file=f)
                print("\ttouch %s"%(rstgt_filename), file=f)
                if stage.requires is not None:
                    for r in stage.requires:
                        self.add_log_string("Dependent on '%s'"%(r.target_name()))
                        ostgt = self.get_makefile_stamp_filename(r)
                        print("%s: %s"%(rstgt_filename,ostgt), file=f)
                        pass
                    pass
                if stage.satisfies is not None:
                    self.add_log_string("Global stage '%s' dependends on repo '%s' stage '%s'"%(stage.satisfies.target_name(), repo.name, stage.name))
                    ostgt_filename = self.get_makefile_stamp_filename(stage.satisfies)
                    print("%s: %s"%(ostgt_filename, rstgt_filename), file=f)
                    pass
                if stage.name in stages:
                    self.add_log_string("Global stage '%s' dependends on repo '%s'"%(stage.name, repo.name))
                    stgt_filename = self.get_makefile_stamp_filename(stages[stage.name])
                    print("%s: %s"%(stgt_filename, rstgt_filename), file=f)
                    pass
                pass
            self.repo_desc_config.fold_repo_stages(None, write_to_makefile)
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
                print('%s=%s ; export %s'%(k,v,k), file=f)
                pass
            pass
        pass
    #f clone
    @classmethod
    def clone(cls, options, repo_url, branch, path=None, dest=None):
        dest_path = dest
        if path is not None:
            if dest_path is not None:
                dest_path = os.path.join(path,dest)
                pass
            else:
                dest_path = path
                pass
            pass
        repo = GitRepo.clone(options, repo_url, new_branch_name="WIP_GRIP", branch=branch, dest=dest_path)
        return cls(repo)
    #f status
    def status(self):
        self.create_subrepos()
        for r in self.subrepos:
            r.status()
            pass
        pass
    #f commit
    def commit(self):
        self.create_subrepos()
        for r in self.subrepos:
            r.commit()
            pass
        self.verbose.message("All subrepos commited")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f fetch
    def fetch(self):
        self.create_subrepos()
        for r in self.subrepos:
            r.fetch()
            pass
        self.verbose.message("All subrepos fetched")
        pass
    #f merge
    def merge(self):
        self.create_subrepos()
        for r in self.subrepos:
            r.merge()
            pass
        self.verbose.message("All subrepos merged")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f publish
    def publish(self, prepush_only=False):
        self.create_subrepos()
        for r in self.subrepos:
            r.prepush()
            pass
        self.verbose.message("All subrepos prepushed")
        if prepush_only: return
        for r in self.subrepos:
            r.push()
            pass
        self.verbose.message("All subrepos pushed")
        self.update_state()
        self.write_state()
        self.verbose.message("Updated state")
        self.verbose.message("**** Now run 'git commit' and 'git push origin HEAD:master' if you wish to commit the GRIP repo itself and push in a 'single' workflow ****")
        pass
    #f All done
