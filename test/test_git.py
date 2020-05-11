#a Imports
import os
from pathlib import Path

from lib.exceptions import *
import lib.os_command
import lib.verbose
from lib.git import Url as GitUrl

from .test_lib.filesystem import FileSystem, FileContent
from .test_lib.loggable import TestLog
from .test_lib.unittest import TestCase
from .test_lib.git import Repository as GitRepository
from .test_lib.grip import Repository as GripRepository
from .test_lib.toml_file import Toml

from typing import List, Optional, Any, ClassVar, Dict

from typing import Dict, Optional, Tuple

OptStr = Optional[str]
#a Unittest for Repo class
class RepoUnitTest(TestCase):
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        TestCase.setUpSubClass(cls)
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        TestCase.tearDownSubClass(cls)
        pass
    def _test_git_url(self, url:str, host:OptStr=None, user:OptStr=None, port:OptStr=None, path:OptStr=None, protocol:OptStr=None, repo_name:OptStr=None) -> None:
        d = GitUrl(url)
        self.assertEqual(d.host,host,"Mismatch in host")
        self.assertEqual(d.user,user,"Mismatch in user")
        self.assertEqual(d.port,port,"Mismatch in port")
        self.assertEqual(d.path,path,"Mismatch in path")
        self.assertEqual(d.protocol,protocol,"Mismatch in protocol")
        self.assertEqual(d.repo_name,repo_name,"Mismatch in repo_name")
        pass
    def _test_git_url_fails(self, *args:Any) -> None:
        self.assertRaises(Exception, GitUrl, *args)
        pass
    def test_paths(self) -> None:
        self._test_git_url("banana.git", host=None, user=None, port=None, path="banana.git", protocol=None, repo_name="banana")
        self._test_git_url("/path/to/banana.git", host=None, user=None, port=None, path="/path/to/banana.git", protocol=None, repo_name="banana")
        self._test_git_url("banana.git/", host=None, user=None, port=None, path="banana.git", protocol=None, repo_name="banana")
        self._test_git_url("/path/to/banana.git/", host=None, user=None, port=None, path="/path/to/banana.git", protocol=None, repo_name="banana")
        pass
    def test_urls(self) -> None:
        self._test_git_url("https://github.com/atthecodeface/grip.git", host="github.com", user=None, port=None, path="atthecodeface/grip.git", protocol="https", repo_name="grip")
        self._test_git_url("http://atthecodeface@github.com/atthecodeface/cdl_hardware.git", host="github.com", user="atthecodeface", port=None, path="atthecodeface/cdl_hardware.git", protocol="http", repo_name="cdl_hardware")
        self._test_git_url("ssh://login@server.com:12345/absolute/path/to/repository", host="server.com", user="login", port="12345", path="absolute/path/to/repository", protocol="ssh", repo_name="repository")
        self._test_git_url("ssh://login@server.com:12345/absolute/path/to/repository/", host="server.com", user="login", port="12345", path="absolute/path/to/repository", protocol="ssh", repo_name="repository")
        pass
    def test_host_paths(self) -> None:
        self._test_git_url("login@server.com:path/to/repository/from/home", host="server.com", user="login", port=None, path="path/to/repository/from/home", protocol=None, repo_name="home")
        self._test_git_url("login@server.com:path/to/repository/from/home/", host="server.com", user="login", port=None, path="path/to/repository/from/home", protocol=None, repo_name="home")
        pass
    def test_mismatches(self) -> None:
        self._test_git_url_fails("ssah://login@server.com:12345/absolute/path/to/repository")
        self._test_git_url_fails("ssh://login@server.com:12345:otherportisnotallowed/absolute/path/to/repository")
        pass
    pass

#a Toplevel
#f Create tests
test_suite = [RepoUnitTest]


