#a Imports
import os, re, unittest
from pathlib import Path
from typing import Type, Dict, Optional, Tuple
from .oscommand import command as os_command
from .oscommand import OSCommandError
from .options import Options
from .exceptions import *

#a Global branchnames
branch_upstream = "upstream"
branch_remote_of_upstream = "%s@{upstream}"%branch_upstream
branch_head = "HEAD"

#a Useful functions
#f git_command
def git_command(options=None, cmd=None, **kwargs) -> str:
    cmd="git %s"%(cmd)
    return os_command(options=options,
                                     cmd=cmd,
                                     **kwargs)

#a Git url class
class GitUrl:
    #v Class properties for git url parsing
    git_protocol_re  = r"(?P<protocol>ssh|git|http|https|ftp|ftps|file)"
    git_user_host_re = r"((?P<user>([a-zA-Z0-9_]*))@|)(?P<host>[a-zA-Z0-9_.]+)"
    git_opt_port_re  = r"(:(?P<port>([0-9]+))|)"
    # git_path_re      = r"(?P<path>([a-zA-Z0-9~._\-/]+))"
    git_path_re      = r"(?P<path>([^:]+))"
    git_repo_url_re        = re.compile( git_protocol_re + r"://" + git_user_host_re + git_opt_port_re + r"/" + git_path_re )
    git_repo_host_path_re  = re.compile( git_user_host_re + ":" + git_path_re )
    git_repo_path_re       = re.compile( git_path_re )
    #t Instance properties
    host     : Optional[str] = None
    user     : Optional[str] = None
    port     : Optional[str] = None
    protocol : Optional[str] = None
    path      : Optional[str] = None
    path_dir  : str
    path_leaf : str
    repo_name : str
    #f __init__
    def __init__(self, git_url:str):
        match  = self.git_repo_url_re.fullmatch(git_url)
        if not match: match = self.git_repo_host_path_re.fullmatch(git_url)
        if not match: match = self.git_repo_path_re.fullmatch(git_url)
        if not match: raise Exception("Failed to parse git URL '%s'"%git_url)
        d = match.groupdict()
        for k in ['protocol','host','user','port','path']:
            if k in d:
                if d[k]!="": setattr(self,k,d[k])
                pass
            pass
        self.parse_path()
        pass
    #f as_string - return 'canonical' string of this url
    def as_string(self) -> str:
        assert self.path is not None
        if (self.protocol is not None) or (self.user is not None) or (self.port is not None):
            assert self.host is not None
            url : str = self.host
            if self.user is not None: url = self.user+"@"+url
            if self.port is not None: url = url+":"+self.port
            return "%s://%s/%s"%(self.protocol, url, self.path)
        if self.host is not None:
            url = self.host
            if self.user is not None: url = self.user+"@"+url
            return "%s/%s"%(url, self.path)
        return self.path
    #f parse_path
    def parse_path(self):
        (d,f) = os.path.split(self.path)
        if f=='': self.path = d
        (path_dir, path_leaf) = os.path.split(self.path)
        self.path_dir = path_dir
        self.path_leaf = path_leaf
        self.repo_name = path_leaf
        if path_leaf[-4:]=='.git': self.repo_name=path_leaf[:-4]
        pass
    #f is_leaf - return True if a file URL and no pathname
    def is_leaf(self) -> bool:
        if self.host is not None: return False
        if self.path_dir != "": return False
        return True
    #f make_relative_to - if .is_leaf() then make relative to another of these
    def make_relative_to(self, abs_url:Type['GitUrl']) -> None:
        assert self.host is None
        assert self.path_dir == ""
        self.host     = abs_url.host
        self.user     = abs_url.user
        self.port     = abs_url.port
        self.protocol = abs_url.protocol
        self.path     = os.path.join(abs_url.path_dir, self.path_leaf)
        self.parse_path()
        pass
    # __str__ - get human readable version
    def __str__(self):
        return "host %s user %s port %s path %s"%(self.host, self.user, self.port, self.path)
    #f All done
    pass

#a GitRepo class
class GitRepo(object):
    """
    A Git repo object for a git repository within the local filesystem
    """
    #t instance properties
    git_url : GitUrl
    path :str
    #f __init__
    def __init__(self, path, git_url=None, permit_no_remote=False, log=None):
        """
        Create the object from a given path

        The path is the local path directory for the repository
        Should chase the path to the toplevel (or do git root)
        Should find the git_url this was cloned from too
        """
        if path is None: path="."
        if not os.path.exists(os.path.abspath(path)):
            raise PathError("path '%s' does not exist"%os.path.abspath(path))
        git_output = git_command(cwd=os.path.abspath(path),
                                 cmd="rev-parse --show-toplevel",
                                 log=log)
        self.path = os.path.realpath(git_output.strip())
        if git_url is None:
            try:
                git_output = git_command(cwd=self.path,
                                         cmd="remote get-url origin",
                                         log=log)
                pass
            except Exception as e:
                if not permit_no_remote: raise e
                git_url = ""
                pass
            git_url = git_output.strip()
            if git_url=="":
                git_url = None
                pass
            else:
                git_url = GitUrl(git_url)
                pass
            pass
        self.git_url = git_url
        (self.upstream_origin, self.upstream_push_branch) = self.get_branch_remote_and_merge(branch_upstream)
        pass
    #f get_branch_remote_and_merge
    def get_branch_remote_and_merge(self, branch_name) -> Tuple[Optional[str], Optional[str]]:
        """
        For a given branch attempt to get remote and merge - i.e. where to fetch/push to
        """
        origin = None
        push_branch = None
        try:
            origin = self.get_config(["branch",branch_name,"remote"])
        except:
            pass
        try:
            push_branch = self.get_config(["branch",branch_name,"merge"])
        except:
            pass
        if push_branch is not None:
            if push_branch[:11]=="refs/heads/":
                push_branch = push_branch[11:]
                pass
            pass
        return (origin, push_branch)
    #f get_name
    def get_name(self) -> str:
        return self.path
    #f get_git_url
    def get_git_url(self):
        return self.git_url
    #f get_git_url_string
    def get_git_url_string(self) -> str:
        return self.git_url.as_string()
    #f get_path
    def get_path(self) -> str:
        return self.path
    #f get_config
    def get_config(self, config_path, log=None) -> str:
        config=".".join(config_path)
        output = git_command(cmd="config --get %s"%config,
                             log=log,
                             cwd=self.path)
        output=output.strip()
        return output
    #f set_upstream_of_branch
    def set_upstream_of_branch(self, branch_name, origin, origin_branch, log=None):
        """
        Set upstream of a branch
        """
        output = git_command(cmd="branch --set-upstream-to=%s/%s '%s'"%(origin, origin_branch, branch_name),
                             log=log,
                             cwd=self.path)
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to set upstream branch for git repo '%s' branch '%s'"%(self.get_name(), branch_name))
        # git branch
    #f get_branch_name - get string branch name from a ref (a branch name)
    def get_branch_name(self, ref="HEAD", log=None) -> str:
        """
        Get changeset of the git repo

        This is more valuable to the user if git repo is_modified() is false.
        """
        output = git_command(cmd="rev-parse --abbrev-ref '%s'"%ref,
                             log=log,
                             cwd=self.path)
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to determine branch for git repo '%s' ref '%s'"%(self.get_name(), ref))
    #f get_cs - get hash of a specified branch
    def get_cs(self, branch_name=None, log=None):
        """
        Get changeset of the git repo

        This is more valuable to the user if git repo is_modified() is false.
        """
        if branch_name is None: branch_name="HEAD"
        output = git_command(cmd="rev-parse '%s'"%branch_name,
                             log=log,
                             cwd=self.path)
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to determine changeset for git repo '%s' branch '%s'"%(self.get_name(), branch_name))
    #f has_cs - determine if it has a changeset or branch
    def has_cs(self, branch_name=None, log=None):
        """
        Determine if a branch/hash is in the repo
        """
        if branch_name is None: branch_name="HEAD"
        (rc,_) = git_command(cmd="rev-parse --verify --quiet %s^{commit}"%branch_name,
                             log=log,
                             cwd=self.path,
                             exception_on_error=False,
                             include_rc=True)
        return rc==0
    #f is_modified
    def is_modified(self, options=None, log=None):
        """
        Return None if the git repo is unmodified since last commit
        Return <how> if the git repo is modified since last commit
        """
        git_command(cmd="update-index -q --refresh",
                    log=log,
                    cwd=self.path)

        if (options is None) or (not options.get("ignore_unmodified",False)):
            output = git_command(cwd=self.path,
                                 log=log,
                                 cmd="diff-index --name-only HEAD")
            output = output.strip()
            if len(output.strip()) > 0:
                return HowFilesModified(output)
            pass

        if (options is None) or (not options.get("ignore_untracked",False)):
            output = git_command(cwd=self.path,
                                 log=log,
                                 cmd="ls-files -o --exclude-standard")
            output = output.strip()
            if len(output.strip()) > 0:
                return HowUntrackedFiles(output)
            pass
        return None
    #f change_branch_ref
    def change_branch_ref(self, branch_name, ref, log=None):
        """
        Change a branch to point to a specific reference

        Used, for example, to make upstream point to a newly fetched head
        """
        output = git_command(cmd="branch -f '%s' '%s'"%(branch_name, ref),
                             log=log,
                             cwd=self.path)
        output = output.strip()
        return output
    #f get_cs_history
    def get_cs_history(self, branch_name="", log=None):
        """
        Get list of changesets of the git repo branch

        This is more valuable to the user if git repo is_modified() is false.
        """
        try:
            output = git_command(cmd="rev-list '%s'"%branch_name,
                                 log=log,
                                 cwd=self.path)
            pass
        except:
            raise HowUnknownBranch("Failed to determine changeset history of '%s' branch for git repo '%s' - is this a properly configured git repo"%(branch_name, self.get_name()))
        output = output.strip()
        output = output.split("\n")
        if len(output) > 0: return output
        raise HowUnknownBranch("No CS histoty returned for '%s' branch for git repo '%s' - is this a properly configured git repo"%(branch_name, self.get_name()))
    #f status
    def status(self, options=None, log=None):
        """
        Get status
        """
        status_option = ""
        if (options is not None) and (options.get("ignore_untracked",False)):
            status_option = "--untracked-files=no"
            pass
        output = git_command(cmd="status --porcelain %s"%status_option,
                             cwd=self.path,
                             log=log,
                             stderr_output_indicates_error=False
        )
        output = output.strip()
        return(output)
    #f fetch
    def fetch(self, log=None):
        """
        Fetch changes from remote
        """
        output = git_command(cmd="fetch",
                             cwd=self.path,
                             log=log,
                             stderr_output_indicates_error=False
        )
        output = output.strip()
        return(output)
    #f rebase
    def rebase(self, options, other_branch, log):
        """
        Rebase branch with other_branch
        """
        cmd_options = ""
        if options.get("interactive",False): cmd_options+=" --interactive"
        try:
            output = git_command(cmd="rebase %s %s"%(cmd_options,other_branch),
                                 cwd=self.path,
                                 log=log,
                                 stderr_output_indicates_error=False
            )
            output = output.strip()
            pass
        except e:
            raise GitReason("rebase failed : %s"%(str(e)))
        return None
    #f push
    def push(self, repo, ref, dry_run=True, log=None ):
        """
        Push to 'repo ref', with optional dry_run
        """
        cmd_options = ""
        if dry_run: cmd_options+=" --dry-run"
        try:
            output = git_command(cmd="push %s '%s' '%s'"%(cmd_options,repo,ref),
                                 cwd=self.path,
                                 log=log,
                                 stderr_output_indicates_error=False
            )
            output = output.strip()
            pass
        except e:
            raise GitReason("push failed : %s"%(str(e)))
        return None
    #f checkout_cs
    def checkout_cs(self, options, changeset):
        """
        Checkout changeset
        """
        output = git_command(options=options,
                             cmd="checkout %s"%(changeset),
                             cwd=self.path,
                             stderr_output_indicates_error=False)
        pass
    #f check_clone_permitted - check if can clone url to path
    @classmethod
    def check_clone_permitted(cls, repo_url, branch=None, dest=None, log=None):
        if log: log.add_entry_string("check to clone from %s branch %s in to %s"%(repo_url, branch, dest))
        if os.path.exists(dest): raise UserError("Cannot clone to %s as it already exists"%(dest))
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir): raise UserError("Cannot clone to %s as the parent directory does not exist"%(dest))
        return True
    #f clone - clone from a Git URL (of a particular branch to a destination directory)
    @classmethod
    def clone(cls, options, repo_url, new_branch_name, branch=None, dest=None, bare=False, depth=None, changeset=None, log=None):
        """
        Clone a branch of a repo_url into a checkout directory
        bare checkouts are used in testing only

        # git clone --depth 1 --single-branch --branch <name> --no-checkout
        # git checkout --detach <changeset>

        """
        url = GitUrl(repo_url)
        if dest is None: dest=url.repo_name
        git_options = []
        if branch is not None: git_options.append( "--branch %s"%branch )
        if (bare is not None) and bare: git_options.append( "--bare") # For TEST only
        if changeset is not None: git_options.append( "--no-checkout")
        if depth is not None:   git_options.append( "--depth %s"%(depth))
        if log: log.add_entry_string("Attempting to clone %s branch %s in to %s"%(repo_url, branch, dest))
        try:
            git_output = git_command(options=options,
                                     log=log,
                                     cmd="clone %s %s %s" % (" ".join(git_options), repo_url, dest),
                                     stderr_output_indicates_error=False)
            pass
        except OSCommandError as e:
            raise UserError("Failed to perform git clone - %s"%(e.cmd.error_output()))
            pass
        try:
            # This can fail if we checked out a tag that is not a branch that is not its own head, as we would be in detached head state
            git_command(options=options, log=log, cwd=dest, cmd="branch --move %s"%branch_upstream)
            pass
        except:
            # If the branch move failed then just create the branch at this head
            git_command(options=options, log=log, cwd=dest, cmd="branch %s HEAD"%branch_upstream)
            pass
        if changeset is None:
            git_command(options=options, log=log, cwd=dest, cmd="branch %s HEAD"%new_branch_name)
            pass
        else:
            try:
                git_command(options=options, log=log, cwd=dest, cmd="branch %s %s"%(new_branch_name, changeset))
                pass
            except:
                raise Exception("Failed to checkout required changeset - maybe depth is not large enough")
            pass
        git_output = git_command(options=options,
                                 log=log,
                                 cwd = dest,
                                 cmd = "checkout %s" % new_branch_name,
                                 stderr_output_indicates_error=False)
        pass
        return cls(dest, git_url=repo_url, log=log)
    #f filename - get filename of full path relative to repo in file system
    def filename(self, paths=[]):
        if type(paths)!=list: paths=[paths]
        filename = self.path
        for p in paths: filename=os.path.join(filename,p)
        return filename
    #f All done
    pass

