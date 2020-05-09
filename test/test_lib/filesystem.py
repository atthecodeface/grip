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
    #f iter_files
    def iter_files(self, path:Path, callback_fn:Callable[[Path],None], glob:str, depth:int) -> None:
        if not path.exists: return
        if path.is_file():
            return callback_fn(path)
            pass
        if not path.is_dir():
            return
        if depth==0:
            return callback_fn(path)
        local_paths = path.glob(glob)
        for p in local_paths:
            self.iter_files(path=p, depth=depth-1, callback_fn=callback_fn, glob=glob)
            pass
        pass
    #f fold_files
    def fold_files(self, hash_dict:Dict[Any,str], path:Path, fold_fn:Callable[[Path],str], glob:str, depth:int, path_name_fn:Callable[[Path],Any]) -> Dict[Any,str]:
        def fold_callback(path:Path)->None:
            hash_name = path_name_fn(path)
            if path.is_file():
                hash_dict[hash_name] = fold_fn(path)
                pass
            else:
                hash_dict[hash_name] = "<dir>"
                pass
            pass
        self.iter_files(path=path, glob=glob, depth=depth, callback_fn=fold_callback)
        return hash_dict
    #f log_hashes
    def log_hashes(self, reason:str, path:Path, glob:str="*", depth:int=0, use_full_name:bool=False) -> None:
        path = self.abspath(path)
        def log_hash(p:Path)->None:
            if p.is_file():
                rel_path = p.relative_to(path)
                hash = md5sum(p)
                self.log.add_log_string("%s: %s : %s"%(reason,str(rel_path), hash))
            pass
        self.iter_files(path=path, glob=glob, depth=depth, callback_fn=log_hash)
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
    def abspath(self, path:Path) -> Path:
        return path.joinpath(self.path, path)
    #f make_dir
    def make_dir(self, path:Path) -> None:
        path = self.abspath(path)
        path.mkdir()
        pass
    #f append_to_file
    def append_to_file(self, path:Path, content:FileContent, mode:str="w+") -> None:
        path = self.abspath(path)
        with path.open(mode) as f:
            f.write(content.content())
            pass
        pass
    #f create_file
    def create_file(self, path:Path, **kwargs:Any) -> None:
        return self.append_to_file(mode="w", path=path, **kwargs)
    #f All done
    pass

