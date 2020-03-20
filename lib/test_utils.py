import unittest
from collections import namedtuple
class TestValues:
    def __init__(self, **kwargs):
        for (k,v) in kwargs.items():
            setattr(self, k, v)
            pass
        pass
    def Get_other_attrs(self):return []
class UnitTestObject(unittest.TestCase):
    def _test_asserts(self, d, akv, reason, has_element_fn, get_element_fn ):
        # print("_test_asserts %s:%s:%s"%(reason, str(akv),str(d)))
        if type(akv) is not dict:
            self.fail("Bug in test - reason '%s' - test data '%s' is not a dictionary (type '%s'), but element is type '%s'"%(reason, str(akv),str(type(akv)),str(type(d))))
            return
        for (k,v) in akv.items():
            if has_element_fn(d,k):
                dv = get_element_fn(d,k)
                if type(dv) in [str,int]:
                    self.assertEqual(dv,v,"Mismatch in %s for key %s"%(reason,k))
                    pass
                elif type(dv) is list:
                    self.assertEqual(dv,v,"List ! %s for key %s"%(reason,k))
                    pass
                elif type(dv) is dict:
                    self._test_dict_asserts(dv,v,"%s.%s"%(reason,k))
                    pass
                else:
                    self._test_obj_asserts(dv,v,"%s.%s"%(reason,k))
                    pass
                pass
            else:
                self.fail("%s (of type %s) expected to have key %s but it did not"%(reason, str(type(d)), k))
                pass
            pass
        pass
    def _test_dict_asserts(self, d, akv, reason ):
        return self._test_asserts(d, akv, reason, has_element_fn=(lambda d,k:k in d), get_element_fn=(lambda d,k:d[k]))
    def _test_obj_asserts(self, d, akv, reason ):
        return self._test_asserts(d, akv, reason, has_element_fn=hasattr, get_element_fn=getattr)
    pass
