#a Unittest for GripRepoState class
from lib.configstate import StateFile

from .test_lib.unittest import UnitTestObject, AKV
from .test_lib.unittest import TestCase

from typing import Dict, Any, Optional, Union

class GripRepoStateUnitTestBase(UnitTestObject):
    state_toml : Optional[str] = None
    config_name : Optional[str] = None
    grs_assert : AKV = {}
    cfg_assert : AKV = {}
    exception_expected = None
    def test_it(self) -> None:
        if self.state_toml is not None:
            grs = StateFile()
            if self.exception_expected is not None:
                self.assertRaises(self.exception_expected, grs.read_toml_string, self.state_toml)
                pass
            else:
                grs.read_toml_string(self.state_toml)
                pass
            if len(self.grs_assert)>0:
                self._test_obj_asserts(grs, self.grs_assert, "grip_repo_state")
                pass
            if self.config_name is not None:
                cfg = grs.select_config(config_name=self.config_name, create_if_new=False)
                if cfg is None:
                    self.assertEqual(cfg, self.cfg_assert)
                    pass
                else:
                    self._test_obj_asserts(cfg, self.cfg_assert, "config_desc")
                    pass
                pass
            pass
        pass
    pass
class GripRepoStateUnitTest1(GripRepoStateUnitTestBase):
    state_toml = """cfga.repo1.changeset="1"\n"""
    grs_assert = {"configs":{"cfga":{"repos":{"repo1":{"changeset":"1"}}}}}
    pass
class GripRepoStateUnitTest2(GripRepoStateUnitTestBase):
    state_toml = """cfga.repo1.changeset="1"\ncfga.repo2.changeset="3"\n"""
    grs_assert = {"configs":{"cfga":{"repos":{"repo2":{"changeset":"3"}}}}}
    pass
class GripRepoStateUnitTestComplex(GripRepoStateUnitTestBase):
    state_toml = """
    cfga.repo1.changeset="1"
    cfga.repo2.changeset="3"
    cfgb.repo3.changeset="apple"
    cfgb.repo1.changeset="banana"
    [cfgc]
    repo1 = {changeset="4"}
    repo2 = {changeset="7"}
    """
    pass
class GripRepoStateUnitTest10(GripRepoStateUnitTestComplex):
    grs_assert = {"configs":{"cfga":{"repos":{
        "repo1":{"changeset":"1"},
        "repo2":{"changeset":"3"},
    }}}}
    pass
class GripRepoStateUnitTest11(GripRepoStateUnitTestComplex):
    grs_assert = {"configs":{"cfgb":{"repos":{
        "repo1":{"changeset":"banana"},
        "repo3":{"changeset":"apple"},
    }}}}
    pass
class GripRepoStateUnitTest12(GripRepoStateUnitTestComplex):
    grs_assert = {"configs":{"cfgc":{"repos":{
        "repo1":{"changeset":"4"},
        "repo2":{"changeset":"7"},
    }}}}
    pass
