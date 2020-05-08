#a Imports
import sys, copy
import toml
from typing import Type, List, Callable, Mapping, Any, Dict, IO, Optional, MutableMapping
RawTomlDict   = MutableMapping[str, Any]
TDFN = Callable[['TomlDictValues', Any, str, Any],Any]

#a Useful functions
#f type_str
def type_str(t : type) -> str:
    if t==str:return "string"
    if t==int:return "integer"
    if t==list:return "list"
    if hasattr(t,"__class__"): return str(t.__class__) #.__name__
    return str(t)

#f str_keys
def str_keys(d:Mapping[str,Any]) -> str:
    return ", ".join([k for k in d.keys()])

#v bool_options
bool_options = {"True":True, "False":False, "Yes":True, "No":False,
                "true":True, "false":False, "yes":True, "no":False}

#a Exceptions
#c TomlError
class TomlError(Exception):
    """
    A TomlError records an error in reading a Toml dictionary.

    *where* is provided by the toml library, indicating (hopefully) where an error started

    *reason* is what is causing the error in TomlDict
    """
    def __init__(self, where:str, reason:str):
        self.where = where
        self.reason = reason
        pass
    def __str__(self) -> str:
        return "%s %s"%(self.where, self.reason)
        pass
    pass

#a Classes
#c TomlDictValues
class TomlDictValues(object):
    """
    This class is used to gather the contents of a toml element,
    based on a description in the TomlDict class.

    It provides mehods to access and extract the data in to an object (or namespace)
    """
    _other_attrs : List[str]
    _dict_class  : Type['TomlDict']
    _parent      : Optional['TomlDictValues']
    #f is_value_instance - class method - determine if an object is a TomlDictValues
    @classmethod
    def is_value_instance(cls:Any, obj:Any) -> bool:
        return isinstance(obj,cls)
    #f __init__ - create TomlDictValues corresponding to a TomlDict
    def __init__(self, dict_class:Type['TomlDict'], parent:Optional['TomlDictValues']=None) -> None:
        self._dict_class = dict_class
        self._parent = parent
        self._other_attrs = []
        pass
    #f Add_other_attr
    def Add_other_attr(self, a:str, v:Any) -> None:
        self._other_attrs.append(a)
        setattr(self, a, v)
        pass
    #f Get_fixed_attrs
    def Get_fixed_attrs(self) -> List[str]:
        return self._dict_class._toml_fixed_attrs()
    #f Get_other_attrs
    def Get_other_attrs(self) -> List[str]:
        return self._other_attrs
    #f Has - determine if we have an attribute
    def Has(self, a:str) -> bool:
        return hasattr(self, a)
    #f IsNone - determine if we don't have an attribute or it is None
    def IsNone(self, a:str) -> bool:
        if not hasattr(self, a): return True
        if getattr(self,a) is None: return True
        return False
    #f Get - get a value from its string name
    def Get(self, a:str) -> Any:
        return getattr(self, a)
    #f Set - set a value from its string name and any value type
    def Set(self, a:str, v:Any) -> None:
        setattr(self, a, v)
        pass
    #f Set_obj_properties - set object propertied according to the string keys
    def Set_obj_properties(self, o:Any, ks:List[str]) -> None:
        for k in ks:
            v = getattr(self,k)
            if v is not None:
                setattr(o, k, v)
                pass
            pass
        pass
    #f Iterate - iterate over all values (as described in the TomlDict class) invoking callback
    def Iterate(self, callback:Callable[['TomlDictValues',str,Any],None], descend_hierarchy:bool=True) -> None:
        avs = self.Get_attr_dict()
        for (x,value) in avs.items():
            if self.is_value_instance(value):
                if descend_hierarchy:
                    value.Iterate(callback)
                else:
                    callback(self,x,value)
                    pass
                pass
            else:
                callback(self,x,value)
                pass
            pass
        pass
    #f Get_attr_dict - get dictionary of <str name> : <value>
    def Get_attr_dict(self) -> Dict[str,Any]:
        attrs = self.Get_fixed_attrs()
        attrs += self._other_attrs
        r = {}
        for a in attrs:
            r[a] = getattr(self,a)
            pass
        return r
    #f Prettyprint - print to stdout
    def Prettyprint(self, prefix:str="", file:IO[str]=sys.stdout) -> None:
        avs = self.Get_attr_dict()
        for (x,value) in avs.items():
            if self.is_value_instance(value):
                value.Prettyprint(prefix = "%s.%s"%(prefix,x), file=file)
                pass
            else:
                print("%s.%s: %s"%(prefix,x,str(value)), file=file)
                pass
            pass
        pass
    #f All done
    pass

#c TomlDict
class TomlDict(object):
    """
    This is a class that is not expected to be instantiated, just subclassed

    The names of properties of a subclass of this will be the keys that a toml dictionary can have.

    The values of those properties should be fn(s, p, msg, v) -> value for TomlDictValues attribute

    If the value function needs to return an error (because v cannot be handled) then it should use msg in the TomlError
    """
    Wildcard : Optional[TDFN] = None
    #f _toml_fixed_attrs - classmethod - get attributes
    @classmethod
    def _toml_fixed_attrs(cls) -> List[str]:
        attrs = dir(cls)
        v = [x for x in attrs if ((x[0]>='a') and (x[0]<='z'))]
        return v
    #f __init__
    __client : Any
    def __init__(self, client:Any) -> None:
        self.__client = client
        pass
    #f All done
    pass

#c TomlDictParser
class TomlDictParser(object):
    """
    This is a namespace for functions that map toml dictionary values to str, bool, or TomlDictValues instances

    This is separated from TomlDict so that TomlDict subclasses properties are ALL permitted toml values
    If these staticmethods were classmethods of TomlDict (or similar) then this would mess that simplicity of description
    """
    #f identity_fn - staticmethod - callback function that returns the value
    @staticmethod
    def identity_fn(s:TomlDictValues, p:Any, m:str, value:Any) -> Any:
        return value
    #f from_dict_attr_value - staticmethod - return function to map value of type t through function fn
    @staticmethod
    def from_dict_attr_value(t : type, fn:Optional[TDFN]=None) -> TDFN:
        true_fn : TDFN = TomlDictParser.identity_fn
        if fn is not None:
            true_fn = fn
            pass
        def f(self:TomlDictValues, parent:Any, msg:str, value:Any) -> Any:
            if type(value)!=t: raise TomlError(msg, "Expected %s but got '%s'"%(type_str(t),str(value)))
            return true_fn(self, parent, msg, value)
        return f
    #f from_dict_attr_bool - classmethod - return function to map value to True/False through global bool_options dictionary
    @classmethod
    def from_dict_attr_bool(cls) -> TDFN:
        def bool_of_str(self:TomlDictValues, parent:Any, msg:str, value:Any) -> bool:
            if value not in bool_options.keys():
                raise TomlError(msg,"Boolean of '%s' is not one of the permitted options %s"%(value, str_keys(bool_options)))
            return bool_options[value]
        return cls.from_dict_attr_value(str,bool_of_str)
    #f from_dict_attr_list - staticmethod - return function to map a list of values through function fn to list of type 't'
    @staticmethod
    def from_dict_attr_list(t : type, fn:Optional[TDFN]=None) -> TDFN:
        true_fn : TDFN = TomlDictParser.identity_fn
        if fn is not None:
            true_fn = fn
            pass
        def f(self:TomlDictValues, parent:Any, msg:str, values:Any) -> Any:
            if type(values)!=list: raise TomlError(msg, "Expected list of %s but got '%s'"%(str(t),str(values)))
            result = []
            for v in values:
                if type(v)!=t: raise TomlError(msg, "Expected %s but got '%s'"%(type_str(t),str(v)))
                result.append(true_fn(self, parent, msg, v))
                pass
            return result
        return f
    #f from_dict_attr_dict - staticmethod - return function to map a dictionary through a TomlDictParser class as a
    @staticmethod
    def from_dict_attr_dict(t:Type[TomlDict]) -> TDFN:
        """
        t must be a subclass of TomlDict
        """
        def f(self:TomlDictValues, parent:Any, msg:str, values:Any) -> Any:
            if not isinstance(values,dict): raise TomlError(msg, "Expected dictionary but got '%s'"%(str(values)))
            return TomlDictParser.from_dict(t, msg, values, parent=parent)
        return f
    #f from_dict - staticmethod - get TomlDictValues instance that parses d with TomlDictParser class cls
    @staticmethod
    def from_dict(cls:Type[TomlDict], msg:str, d:RawTomlDict, parent:Optional[TomlDictValues]=None) -> TomlDictValues:
        values = TomlDictValues(dict_class=cls, parent=parent)
        attrs = cls._toml_fixed_attrs()
        rtd = copy.deepcopy(d)
        for x in attrs:
            if x in rtd:
                values_fn = getattr(cls,x)
                setattr(values, x, values_fn(values, parent, "%s.%s"%(msg,x), rtd[x]))
                del(rtd[x])
                pass
            else:
                setattr(values, x, None)
            pass
        if cls.Wildcard is not None:
            for x in rtd:
                v = cls.Wildcard(values, parent, "%s.%s"%(msg,x), rtd[x])
                values.Add_other_attr(x,v)
                pass
            rtd = {}
            pass
        if len(rtd)>0:
            r = []
            for a in rtd.keys(): r.append(a)
            raise TomlError(msg, "Unparsed keys '%s'"%(" ".join(r)))
        return values

