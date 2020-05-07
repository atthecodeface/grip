#a Imports
import os, re, unittest
from typing import Dict, Optional, Tuple
import lib.oscommand, lib.verbose
from .exceptions import *

#a Unittest for Repo class
class RepoUnitTest(unittest.TestCase):
    def _test_git_url(self, url, host=None, user=None, port=None, path=None, protocol=None, repo_name=None):
        d = GitRepo.parse_git_url(url)
        self.assertEqual(d.host,host,"Mismatch in host")
        self.assertEqual(d.user,user,"Mismatch in user")
        self.assertEqual(d.port,port,"Mismatch in port")
        self.assertEqual(d.path,path,"Mismatch in path")
        self.assertEqual(d.protocol,protocol,"Mismatch in protocol")
        self.assertEqual(d.repo_name,repo_name,"Mismatch in repo_name")
        pass
    def _test_git_url_fails(self, *args):
        self.assertRaises(Exception, GitRepo.parse_git_url, *args)
        pass
    def test_paths(self):
        self._test_git_url("banana.git", host=None, user=None, port=None, path="banana.git", protocol=None, repo_name="banana")
        self._test_git_url("/path/to/banana.git", host=None, user=None, port=None, path="/path/to/banana.git", protocol=None, repo_name="banana")
        self._test_git_url("banana.git/", host=None, user=None, port=None, path="banana.git", protocol=None, repo_name="banana")
        self._test_git_url("/path/to/banana.git/", host=None, user=None, port=None, path="/path/to/banana.git", protocol=None, repo_name="banana")
        pass
    def test_urls(self):
        self._test_git_url("https://github.com/atthecodeface/grip.git", host="github.com", user=None, port=None, path="atthecodeface/grip.git", protocol="https", repo_name="grip")
        self._test_git_url("http://atthecodeface@github.com/atthecodeface/cdl_hardware.git", host="github.com", user="atthecodeface", port=None, path="atthecodeface/cdl_hardware.git", protocol="http", repo_name="cdl_hardware")
        self._test_git_url("ssh://login@server.com:12345/absolute/path/to/repository", host="server.com", user="login", port="12345", path="absolute/path/to/repository", protocol="ssh", repo_name="repository")
        self._test_git_url("ssh://login@server.com:12345/absolute/path/to/repository/", host="server.com", user="login", port="12345", path="absolute/path/to/repository", protocol="ssh", repo_name="repository")
        pass
    def test_host_paths(self):
        self._test_git_url("login@server.com:path/to/repository/from/home", host="server.com", user="login", port=None, path="path/to/repository/from/home", protocol=None, repo_name="home")
        self._test_git_url("login@server.com:path/to/repository/from/home/", host="server.com", user="login", port=None, path="path/to/repository/from/home", protocol=None, repo_name="home")
        pass
    def test_mismatches(self):
        self._test_git_url_fails("ssah://login@server.com:12345/absolute/path/to/repository")
        self._test_git_url_fails("ssh://login@server.com:12345:otherportisnotallowed/absolute/path/to/repository")
        pass
    pass


