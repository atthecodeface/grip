#a Imports
import os, shlex
from .git import GitRepo
from .repodesc import GripRepoDesc
from .repostate import GripRepoState
from .repoconfig import GripRepoConfig
from .workflows import workflows

def pp_stdout(acc, s, indent=0):
    print("  "*indent+acc+s)
    return ""

#a Classes
#c GripSubrepo class
class GripSubrepo:
    ws = workflows()
    def __init__(self, grip_repo, repo_desc):
        self.name = repo_desc.name
        self.grip_repo = grip_repo
        self.git_repo = GitRepo(path=grip_repo.git_repo.filename([repo_desc.path]))
        self.workflow = repo_desc.workflow()
        pass
    def install_hooks(self):
        pass
    def commit(self):
        try:
            print("Commiting repo '%s' with workflow '%s'"%(self.name, self.workflow.name))
            okay = self.workflow.commit(self.grip_repo, self.git_repo)
            if not okay: raise(Exception("Commit for repo '%s' not permitted"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    def fetch(self):
        try:
            print("Fetching repo '%s' with workflow '%s'"%(self.name, self.workflow.name))
            okay = self.workflow.fetch(self.grip_repo, self.git_repo)
            if not okay: raise(Exception("Fetch for repo '%s' not permitted"%self.name))
            pass
        except Exception as e:
            raise(e)
        pass
    def get_cs(self):
        return self.git_repo.get_cs()
    pass
#c GripRepo class
class GripRepo:
    #v Static properties
    grip_dir_name = ".grip"
    grip_toml_filename   = "grip.toml"
    state_toml_filename  = "state.toml"
    config_toml_filename = "local.config.toml"
    grip_env_filename    = "local.env.sh"
    makefile_targets_dirname = "local.makefile_targets"
    grip_makefile_filename = "local.grip_makefile"
    grip_makefile_env_filename = "local.grip_makefile.env"
    #f find_git_repo_of_grip_root
    @staticmethod
    def find_git_repo_of_grip_root(path):
        git_repo = GitRepo(path)
        path = git_repo.get_path()
        if not os.path.isdir(os.path.join(path,".grip")):
            path = os.path.dirname(path)
            return GripRepo.find_git_repo_of_grip_root(path)
        return git_repo
    #f __init__
    def __init__(self, git_repo=None, path=None, ensure_configured=False):
        if git_repo is None:
            git_repo = GripRepo.find_git_repo_of_grip_root(path)
            pass
        if git_repo is None:
            raise Exception("Not within a git repository, so not within a grip repository either")
        self.git_repo = git_repo
        self.repo_desc        = None
        self.repo_state       = None
        self.repo_desc_config = None
        self.config_state     = None
        self.subrepos         = None
        self.read_desc()
        self.read_state()
        self.read_config()
        if ensure_configured:
            # self.repo_desc.prettyprint("",pp_stdout)
            # self.repo_state.prettyprint("",pp_stdout)
            # self.repo_config.prettyprint("",pp_stdout)
            if self.repo_desc_config is None:
                raise Exception("Unconfigured (or misconfigured) grip repository - has this grip repo been configured yet?")
            if self.config_state is None:
                raise Exception("Unconfigured (or misconfigured) grip repository - has this grip repo been configured yet?")
            pass
        self.grip_git_url = None
        # if self.repo_config is not None:   self.grip_git_url = self.repo_config.grip_git_url
        if self.grip_git_url is None:      self.grip_git_url = git_repo.get_git_url()
        if self.grip_git_url is not None: 
            self.repo_desc.resolve_git_urls(self.grip_git_url)
            pass
        # self.repo_desc.prettyprint("",pp_stdout)        
        pass
    #f grip_path
    def grip_path(self, filename):
        return self.git_repo.filename([self.grip_dir_name, filename])
    #f read_desc
    def read_desc(self):
        self.repo_desc = GripRepoDesc(git_repo=self.git_repo)
        self.repo_desc.read_toml_file(self.grip_path(self.grip_toml_filename))
        self.branch_name = "WIP_%s"%(self.repo_desc.name)
        pass
    #f read_state
    def read_state(self):
        self.repo_state = GripRepoState()
        self.repo_state.read_toml_file(self.grip_path(self.state_toml_filename))
        pass
    #f read_config
    def read_config(self):
        self.repo_config = GripRepoConfig()
        self.repo_config.read_toml_file(self.grip_path(self.config_toml_filename))
        if self.repo_config.config is not None:
            config_name = self.repo_config.config
            config = self.repo_desc.select_config(config_name)
            if config is None: raise Exception("Read config.toml indicating grip configuration is '%s' but that is not in the grip.toml description"%config_name)
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
        self.repo_state.write_toml_file(self.grip_path(self.state_toml_filename))
        pass
    #f update_config
    def update_config(self):
        self.repo_config.config       = self.repo_desc_config.name
        self.repo_config.grip_git_url = self.grip_git_url.git_url()
        pass
    #f write_config
    def write_config(self):
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
            raise Exception("Grip repository is already configured - cannot configure it again, a new clone of the grip repo must be used instead")
        config = self.repo_desc.select_config(config_name)
        if config is None: raise Exception("Could not select grip config '%s'; is it defined in the grip.toml file?"%config_name)
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
        self.update_config()
        self.write_config()
        self.grip_env_write()
        self.create_grip_makefiles()
        pass
    #f check_clone_permitted
    def check_clone_permitted(self):
        for r in self.repo_desc_config.iter_repos():
            dest = self.git_repo.filename([r.path])
            if not GitRepo.check_clone_permitted(r.url, branch=r.branch, dest=dest):
                raise Exception("Not permitted to clone '%s' to  '%s"%(r.url, dest))
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
            print("Cloning '%s' branch '%s' cs '%s' in to path '%s'"%(r.get_git_url_string(), r_state.branch, r_state.changeset, dest))
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
        # clean out make targets
        pass
    #f get_makefile_target
    def get_makefile_target(self,s,r=None):
        if r is not None: s=s+"."+r
        return os.path.join(self.grip_path(self.makefile_targets_dirname), s)
    #f new_makefile_target
    def new_makefile_target(self,s,r=None):
        stgt = self.get_makefile_target(s,r)
        if os.path.exists(stgt):
            os.unlink(stgt)
            pass
        return stgt
    #f create_grip_makefiles
    def create_grip_makefiles(self):
        """
        Repositories are all ready.
        Create makefile target directory
        Create makefile.env and makefile
        Delete makefile targets
        """
        makefile_targets = self.grip_path(self.makefile_targets_dirname)
        try:
            os.mkdir(makefile_targets)
            pass
        except FileExistsError:
            pass
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
        with open(self.grip_path(self.grip_makefile_filename),"w") as f:
            print("-include %s"%(self.grip_path(self.grip_makefile_env_filename)), file=f)
            stages = self.repo_desc_config.get_stages()
            for s in stages:
                stgt = self.new_makefile_target(s)
                print("\n.PHONY: %s"%(s), file=f)
                print("%s: %s"%(s, stgt), file=f)
                print("\n%s:"%(stgt), file=f)
                print("\ttouch %s"%(stgt), file=f)
                pass
            def write_to_makefile(repo, stage):
                stgt = self.get_makefile_target(stage.name)
                rstgt = self.new_makefile_target(stage.name,repo.name)
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
                print("%s: %s"%(stgt, rstgt), file=f)
                print("%s:"%(rstgt), file=f)
                print("\t$(GRIP_%s_%s_ENV) cd %s && (%s)"%(repo.name, stage.name, wd, exec), file=f)
                print("\ttouch %s"%(rstgt), file=f)
                if stage.requires is not None:
                    for r in stage.requires:
                        r = r.split(".")
                        stage = r[0]
                        repo = None
                        if len(r)==2:
                            repo = r[0]
                            stage = r[1]
                            pass
                        if repo is None:
                            ostgt = self.get_makefile_target(stage)
                            print("%s: %s"%(rstgt,ostgt), file=f)
                            pass
                        else:
                            ostgt = self.get_makefile_target(stage,repo)
                            print("%s: %s"%(rstgt,ostgt), file=f)
                            pass
                        pass
                    pass
                pass
            self.repo_desc_config.get_repo_stages(write_to_makefile)
            pass
        # clean out make targets
        pass
    #f commit
    def commit(self, options):
        self.create_subrepos()
        for r in self.subrepos:
            r.commit()
            pass
        print("All subrepos commited")
        self.update_state()
        self.write_state()
        print("Updated state")
        print("**** Now run git commit if you wish to commit the GRIP repo itself ****")
        pass
    #f fetch
    def fetch(self, options):
        self.create_subrepos()
        for r in self.subrepos:
            r.fetch()
            pass
        print("All subrepos fetched")
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
