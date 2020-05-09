#!/usr/bin/env python3
"""
File system for tests so they can run in cleanly
"""

#a Imports
import os, tempfile
from typing import List, Callable, Optional, Any, ClassVar, cast
PathList = List[str]

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
    path : str
    #f __init__
    def __init__(self, use_dir:Optional[str]=None) -> None:
        if use_dir is None:
            self.tmp_dir = tempfile.TemporaryDirectory(suffix=".grip_test_dir")
            self.path = self.tmp_dir.name
            pass
        else:
            self.path = use_dir
            pass
        pass
    #f cleanup
    def cleanup(self) -> None:
        if hasattr(self,"tmp_dir"):
            self.tmp_dir.cleanup()
            del(self.tmp_dir)
            del(self.path)
            pass
        pass
    #f abspath
    def abspath(self, paths:PathList) -> str:
        path = self.path
        for p in paths: path=os.path.join(path, p)
        return path
    #f make_dir
    def make_dir(self, paths:PathList) -> None:
        path = self.abspath(paths)
        os.mkdir(path)
        pass
    #f append_to_file
    def append_to_file(self, paths:PathList, content:FileContent, mode:str="w+") -> None:
        path = self.abspath(paths)
        with open(path,mode) as f:
            f.write(content.content())
            pass
        pass
    #f create_file
    def create_file(self, **kwargs:Any) -> None:
        return self.append_to_file(mode="w", **kwargs)
    #f All done
    pass

