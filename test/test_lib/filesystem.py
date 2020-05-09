#!/usr/bin/env python3
"""
File system for tests so they can run in cleanly
"""

#a Imports
import os, tempfile
from pathlib import Path
from hashlib import md5
from .loggable import TestLog

from typing import List, Callable, Optional, Any, Dict
PathList = List[str]

def md5sum(path:Path)->str:
    hash = md5()
    with path.open("rb") as f:
        data = f.read(4096)
        while len(data)>0:
            hash.update(data)
            data = f.read(4096)
            pass
        pass
    return hash.hexdigest()

class FileContent:
    init_str : str
    def __init__(self, init_str:str=""):
        self.init_str = init_str
        pass
    def content(self) -> str:
        return self.init_str
    pass
class EmptyContent(FileContent):
    pass

#c 'file system' class
class FileSystem(object):
    """
    A class for tests to use as a filesystem - include methods such as 'make_dir', 'create_file', and 'open'
    The class generates a temp directory which should be removed by calling 'cleanup'
    """
    path : Path
    #f __init__
    def __init__(self, log:TestLog, use_dir:Optional[str]=None) -> None:
        self.log = log
        if use_dir is None:
            self.tmp_dir = tempfile.TemporaryDirectory(suffix=".grip_test_dir")
            self.path = Path(self.tmp_dir.name)
            pass
        else:
            self.path = Path(use_dir)
            pass
        self.log.add_log_string("Fs: created '%s'"%(str(self.path)))
        pass
    #f fold_files
    def fold_files(self, hash_dict:Dict[Any,str], path:Path, fold_fn:Callable[[Path],str], glob:str, depth:int, path_name_fn:Callable[[Path],Any]) -> Dict[Any,str]:
        hash_name = path_name_fn(path)
        if not path.exists: return hash_dict
        if path.is_file():
            hash_dict[hash_name] = fold_fn(path)
            pass
        if not path.is_dir():
            return hash_dict
        if depth==0:
            hash_dict[hash_name] = "<dir>"
            return hash_dict
        local_paths = path.glob(glob)
        for p in local_paths:
            self.fold_files(hash_dict, p, fold_fn=fold_fn, glob=glob, depth=depth-1, path_name_fn=path_name_fn)
            pass
        return hash_dict
    #f log_hashes
    def log_hashes(self, reason:str, path:Path, glob:str="*", depth:int=0, use_full_name:bool=False) -> None:
        path = self.path.joinpath(path)
        d = self.fold_files({}, path=path, fold_fn=md5sum, glob=glob, depth=depth, path_name_fn=lambda p:str(p.relative_to(path)))
        for (k,v) in d.items():
            self.log.add_log_string("%s: %s : %s"%(reason,k,v))
            pass
        pass
    #f cleanup
    def cleanup(self) -> None:
        if hasattr(self,"path"):
            self.log.add_log_string("Fs: cleaning up '%s'"%str(self.path))
            del(self.path)
            pass
        if hasattr(self,"tmp_dir"):
            self.tmp_dir.cleanup()
            del(self.tmp_dir)
            pass
        pass
    #f abspath
    def abspath(self, paths:PathList) -> Path:
        path = self.path
        for p in paths: path=path.joinpath(path, Path(p))
        return path
    #f make_dir
    def make_dir(self, paths:PathList) -> None:
        path = self.abspath(paths)
        path.mkdir()
        pass
    #f append_to_file
    def append_to_file(self, paths:PathList, content:FileContent, mode:str="w+") -> None:
        path = self.abspath(paths)
        with path.open(mode) as f:
            f.write(content.content())
            pass
        pass
    #f create_file
    def create_file(self, **kwargs:Any) -> None:
        return self.append_to_file(mode="w", **kwargs)
    #f All done
    pass

