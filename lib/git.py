#a Imports
import os, re, unittest
from pathlib import Path, PurePath
from typing import Type, Dict, Optional, Tuple, Any, List, Union, cast
from .os_command import OSCommand
OSCommandError = OSCommand.Error
from .options import Options
from .log import Log
from .exceptions import *

#a Global branchnames
branch_upstream = "upstream"
branch_remote_of_upstream = "%s@{upstream}"%branch_upstream
branch_head = "HEAD"

#a Useful functions
#f global_git_command
def global_git_command(cmd:str="", cwd:Optional[Path]=None, **kwargs:Any) -> OSCommand:
    if cwd is None: cmd_cwd=Path()
    else: cmd_cwd=cwd
    return OSCommand(cmd="git %s"%(cmd), cwd=str(cmd_cwd), **kwargs).run()

#a Classes
#c Git url class
class Url:
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
    path      : PurePath
    path_has_dir : bool # True once parsed if path has a directory element
    path_dir  : PurePath # Ignore if path_has_dir is False
    path_leaf : str
    repo_name : str
    #f __init__
    def __init__(self, git_url:str):
        match  = self.git_repo_url_re.fullmatch(git_url)
        if not match: match = self.git_repo_host_path_re.fullmatch(git_url)
        if not match: match = self.git_repo_path_re.fullmatch(git_url)
        if not match: raise Exception("Failed to parse git URL '%s'"%git_url)
        d = match.groupdict()
        if "path" not in d: raise Exception("Bug - git url parse re must have a 'path' group")
        self.path=PurePath(d["path"])
        for k in ['protocol','host','user','port']:
            if k in d:
                if d[k]!="": setattr(self,k,d[k])
                pass
            pass
        self.parse_path()
        pass
    #f as_string - return 'canonical' string of this url
    def as_string(self) -> str:
        if (self.protocol is not None) or (self.user is not None) or (self.port is not None):
            assert self.host is not None
            url : str = self.host
            if self.user is not None: url = self.user+"@"+url
            if self.port is not None: url = url+":"+self.port
            return "%s://%s/%s"%(self.protocol, url, self.path)
        if self.host is not None:
            url = self.host
            if self.user is not None: url = self.user+"@"+url
            return "%s/%s"%(url, str(self.path))
        return str(self.path)
    #f parse_path
    def parse_path(self) -> None:
        self.path_leaf    = self.path.name
        self.path_has_dir = (self.path_leaf != str(self.path))
        self.path_dir     = self.path.parent
        self.repo_name    = self.path_leaf
        if self.path.suffix=='.git': self.repo_name=self.path.stem
        pass
    #f is_leaf - return True if a file URL and no pathname
    def is_leaf(self) -> bool:
        if self.host is not None: return False
        return not self.path_has_dir
    #f make_relative_to - if .is_leaf() then make relative to another of these
    def make_relative_to(self, abs_url:'Url') -> None:
        assert self.is_leaf()
        self.host     = abs_url.host
        self.user     = abs_url.user
        self.port     = abs_url.port
        self.protocol = abs_url.protocol
        self.path     = Path(abs_url.path_dir).joinpath(self.path_leaf)
        self.parse_path()
        pass
    # __str__ - get human readable version
    def __str__(self) -> str:
        return "host %s user %s port %s path %s"%(self.host, self.user, self.port, self.path)
    #f All done
    pass

#c Git remote (origin and branch)
class Remote(object):
    origin : str
    branch : str
    def __init__(self, origin:str, branch:str):
        if branch[:11]=="refs/heads/":
            branch = branch[11:]
            pass
        self.origin = origin
        self.branch = branch
        pass
    def get_origin(self) -> str: return self.origin
    def get_branch(self) -> str: return self.branch

#c Repository class
class Repository(object):
    """
    A Git repo object for a git repository within the local filesystem
    """
    #t instance properties
    git_url  : str
    url      : Url
    upstream : Optional[Remote]
    _path     : Path
    options  : Options
    log      : Log
    #f git_os_command
    def git_os_command(self, cwd:Optional[Path]=None, cmd:str="", **kwargs:Any) -> OSCommand:
        if cwd is None:
            cwd = self._path
            pass
        return OSCommand( log     = self.log,
                          cmd     = "git %s"%(cmd),
                          cwd     = str(cwd),
                          **kwargs).run()

    #f git_command
    def git_command(self, stderr_output_indicates_error:bool=True, exception_on_error:bool=True, **kwargs:Any) -> str:
        cmd = self.git_os_command(**kwargs)
        return cmd.check_results(stderr_output_indicates_error=stderr_output_indicates_error, exception_on_error=exception_on_error)

    #f __init__
    def __init__(self, path:Path, git_url:Optional[str]=None, permit_no_remote:bool=False, log:Optional[Log]=None, options:Optional[Options]=None):
        """
        Create the object from a given path

        The path is the local path directory for the repository
        Should chase the path to the toplevel (or do git root)
        Should find the git_url this was cloned from too
        """
        if log is None: log=Log()
        if options is None: options=Options()
        self.log = log
        self.options = options
        if path.is_file(): path=path.parent
        if not path.exists():
            raise PathError("path '%s' does not exist"%str(path))
        git_output = self.git_command(cwd=path, cmd="rev-parse --show-toplevel")
        self._path = Path(git_output.strip())
        if git_url is None:
            try:
                git_output = self.git_command(cmd="remote get-url origin")
                pass
            except Exception as e:
                if not permit_no_remote: raise e
                git_url = ""
                pass
            git_url = git_output.strip()
            pass
        self.git_url = git_url
        self.url = Url(git_url)
        self.upstream = self.get_branch_remote_and_merge(branch_upstream)
        pass
    #f check_clone_permitted - check if can clone url to path
    @classmethod
    def check_clone_permitted(cls, repo_url:str, dest:Path, branch:Optional[str], log:Optional[Log]=None) -> bool:
        if branch is None: branch="<none>"
        if log: log.add_entry_string("check to clone from %s branch %s in to %s"%(repo_url, branch, str(dest)))
        if dest.exists(): raise UserError("Cannot clone to %s as it already exists"%(str(dest)))
        dest_dir = dest.parent
        if not dest_dir.is_dir(): raise UserError("Cannot clone to %s as the parent directory does not exist"%(str(dest)))
        return True
    #f clone - clone from a Git URL (of a particular branch to a destination directory)
    @classmethod
    def clone(cls, repo_url:str, new_branch_name:str, dest:Optional[Path]=None, branch:Optional[str]=None, bare:bool=False, depth:Optional[int]=None, changeset:Optional[str]=None, options:Optional[Options]=None, log:Optional[Log]=None) -> 'Repository':
        """
        Clone a branch of a repo_url into a checkout directory
        bare checkouts are used in testing only

        # git clone --depth 1 --single-branch --branch <name> --no-checkout
        # git checkout --detach <changeset>

        """
        url = Url(repo_url)
        if dest is None: dest=Path(url.repo_name)
        git_options = []
        if branch is not None: git_options.append( "--branch %s"%branch )
        if (bare is not None) and bare: git_options.append( "--bare") # For TEST only
        if changeset is not None: git_options.append( "--no-checkout")
        if depth is not None:   git_options.append( "--depth %s"%(depth))
        if log: log.add_entry_string("Attempting to clone %s branch %s in to %s"%(repo_url, branch, str(dest)))
        git_cmd = global_git_command(log=log,
                                     cmd="clone %s %s %s" % (" ".join(git_options), repo_url, str(dest)))
        if git_cmd.rc()!=0:
            raise UserError("Failed to perform git clone - %s"%(git_cmd.stderr()))
        if bare: return cls(path=dest, git_url=repo_url, log=log)
        git_cmd = global_git_command(log=log, cwd=dest, cmd="rev-parse --verify --quiet %s^{commit}"%branch_upstream)
        if git_cmd.rc()==0:
            if log: log.add_entry_string("Already has branch '%s' - delete it before it causes trouble"%branch_upstream)
            global_git_command(log=log, cwd=dest, cmd="branch --delete %s"%branch_upstream)
            pass
        git_cmd = global_git_command(log=log, cwd=dest, cmd="branch --move %s"%branch_upstream)
        if git_cmd.rc()==0:
            # If the branch move failed then just create the branch at this head
            global_git_command(log=log, cwd=dest, cmd="branch %s HEAD"%branch_upstream)
            pass
        if changeset is None:
            global_git_command(log=log, cwd=dest, cmd="branch %s HEAD"%new_branch_name)
            pass
        else:
            git_cmd = global_git_command(log=log, cwd=dest, cmd="branch %s %s"%(new_branch_name, changeset))
            if git_cmd.rc()!=0: raise Exception("Failed to point branch %s at required changeset %s - maybe depth is not large enough"%(new_branch_name, changeset))
            pass
        git_cmd = global_git_command(log=log,
                                        cwd = dest,
                                        cmd = "checkout %s" % new_branch_name)
        if git_cmd.rc()!=0:
                raise Exception("Failed to checkout required changeset - maybe depth is not large enough")
        return cls(path=Path(dest), git_url=repo_url, log=log, options=options)
    #f get_upstream - get Remote corresponding to the upstream
    def get_upstream(self) -> Optional[Remote]:
        return self.upstream
    #f get_branch_remote_and_merge
    def get_branch_remote_and_merge(self, branch_name:str) -> Optional[Remote]:
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
        if origin is None or push_branch is None: return None
        return Remote(origin, push_branch)
    #f get_name
    def get_name(self) -> str:
        return str(self._path)
    #f get_git_url
    def get_git_url(self) -> Url:
        return self.url
    #f get_git_url_string
    def get_git_url_string(self) -> str:
        return self.url.as_string()
    #f get_config
    def get_config(self, config_path:List[str]) -> str:
        config=".".join(config_path)
        return self.git_command(cmd="config --get %s"%config).strip()
    #f set_upstream_of_branch
    def set_upstream_of_branch(self, branch_name:str, remote:Remote) -> str:
        """
        Set upstream of a branch
        """
        output = self.git_command(cmd="branch --set-upstream-to=%s/%s '%s'"%(remote.get_origin(), remote.get_branch(), branch_name))
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to set upstream branch for git repo '%s' branch '%s'"%(self.get_name(), branch_name))
    #f get_branch_name - get string branch name from a ref (a branch name)
    def get_branch_name(self, ref:str="HEAD") -> str:
        """
        Get changeset of the git repo

        This is more valuable to the user if git repo is_modified() is false.
        """
        output = self.git_command(cmd="rev-parse --abbrev-ref '%s'"%ref)
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to determine branch for git repo '%s' ref '%s'"%(self.get_name(), ref))
    #f get_cs - get hash of a specified branch
    def get_cs(self, branch_name:Optional[str]=None) -> str:
        """
        Get changeset of the git repo

        This is more valuable to the user if git repo is_modified() is false.
        """
        if branch_name is None: branch_name="HEAD"
        output = self.git_command(cmd="rev-parse '%s'"%branch_name)
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to determine changeset for git repo '%s' branch '%s'"%(self.get_name(), branch_name))
    #f has_cs - determine if it has a changeset or branch
    def has_cs(self, branch_name:Optional[str]=None) -> bool:
        """
        Determine if a branch/hash is in the repo
        """
        if branch_name is None: branch_name="HEAD"
        git_cmd = self.git_os_command(cmd="rev-parse --verify --quiet %s^{commit}"%branch_name)
        return git_cmd.rc()==0
    #f is_modified
    def is_modified(self) -> Optional[GitReason]:
        """
        Return None if the git repo is unmodified since last commit
        Return <how> if the git repo is modified since last commit
        """
        self.git_command(cmd="update-index -q --refresh")

        if not self.options.get("ignore_unmodified",False):
            output = self.git_command(cmd="diff-index --name-only HEAD")
            output = output.strip()
            if len(output.strip()) > 0:
                return HowFilesModified(output)
            pass

        if not self.options.get("ignore_untracked",False):
            output = self.git_command(cmd="ls-files -o --exclude-standard")
            output = output.strip()
            if len(output.strip()) > 0:
                return HowUntrackedFiles(output)
            pass
        return None
    #f change_branch_ref
    def change_branch_ref(self, branch_name:str, ref:str)->str:
        """
        Change a branch to point to a specific reference

        Used, for example, to make upstream point to a newly fetched head
        """
        return self.git_command(cmd="branch -f '%s' '%s'"%(branch_name, ref)).strip()
    #f get_cs_history
    def get_cs_history(self, branch_name:str="") -> List[str]:
        """
        Get list of changesets of the git repo branch

        This is more valuable to the user if git repo is_modified() is false.
        """
        try:
            output = self.git_command(cmd="rev-list '%s'"%branch_name)
            pass
        except:
            raise HowUnknownBranch("Failed to determine changeset history of '%s' branch for git repo '%s' - is this a properly configured git repo"%(branch_name, self.get_name()))
        output = output.strip()
        cs_list = output.split("\n")
        if len(cs_list) > 0: return cs_list
        raise HowUnknownBranch("No CS histoty returned for '%s' branch for git repo '%s' - is this a properly configured git repo"%(branch_name, self.get_name()))
    #f status
    def status(self) -> str:
        """
        Get status
        """
        status_option = ""
        if self.options.get("ignore_untracked",False):
            status_option = "--untracked-files=no"
            pass
        output = self.git_command(cmd="status --porcelain %s"%status_option,
                                  stderr_output_indicates_error=False )
        output = output.strip()
        return(output)
    #f fetch
    def fetch(self) -> str:
        """
        Fetch changes from remote
        """
        output = self.git_command(cmd="fetch",
                                  stderr_output_indicates_error=False
        )
        output = output.strip()
        return output
    #f rebase
    def rebase(self, other_branch:str) -> Optional[GitReason]:
        """
        Rebase branch with other_branch
        """
        cmd_options = ""
        if self.options.get("interactive",False): cmd_options+=" --interactive"
        try:
            output = self.git_command(cmd="rebase %s %s"%(cmd_options,other_branch),
                                      stderr_output_indicates_error=False)
            output = output.strip()
            pass
        except Exception as e:
            return GitReason("rebase failed : %s"%(str(e)))
        return None
    #f commit
    def commit(self) -> str:
        """
        Commit
        """
        cmd_options = "-a "
        if self.options.has("message"):
            cmd_options+=" -m '%s'"%(self.options.get("message"))
        try:
            output = self.git_command(cmd="commit %s"%(cmd_options))
            output = output.strip()
            pass
        except Exception as e:
            raise GitReason("commit failed : %s"%(str(e)))
        return output
    #f push
    def push(self, repo:str, ref:str, dry_run:bool=True ) -> None:
        """
        Push to 'repo ref', with optional dry_run
        """
        cmd_options = ""
        if dry_run: cmd_options+=" --dry-run"
        try:
            output = self.git_command(cmd="push %s '%s' '%s'"%(cmd_options,repo,ref),
                                      stderr_output_indicates_error=False)
            output = output.strip()
            pass
        except Exception as e:
            raise GitReason("push failed : %s"%(str(e)))
        return None
    #f checkout_cs
    def checkout_cs(self, changeset:str) -> None:
        """
        Checkout changeset
        """
        self.git_command(cmd="checkout %s"%(changeset), stderr_output_indicates_error=False)
        pass
    #f path - get a path relative to the repository
    def path(self, path:Optional[Path]=None) -> Path:
        if path is None: return self._path
        return self._path.joinpath(path)
    #f All done
    pass

