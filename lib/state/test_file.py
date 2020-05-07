#a Unittest for GripRepoState class
from typing import Dict, Any, Optional, Union
from ..test_utils import UnitTestObject
class GripRepoStateUnitTestBase(UnitTestObject):
    state_toml : Optional[str] = None
    config_name : Union[bool, None, str] = False
    grs_assert : Optional[Dict[str,Any]] = None
    cfg_assert = None
    exception_expected = None
    def test_it(self):
        if self.state_toml is not None:
            grs = GripRepoState()
            if self.exception_expected is not None:
                self.assertRaises(self.exception_expected, grs.read_toml_string, self.state_toml)
                pass
            else:
                grs.read_toml_string(self.state_toml)
                pass
            if self.grs_assert is not None:
                self._test_obj_asserts(grs, self.grs_assert, "grip_repo_state")
                pass
            if self.config_name is not False:
                cfg = grs.select_config(config_name=self.config_name)
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
