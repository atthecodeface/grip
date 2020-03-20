#a Imports
import toml, copy

#a Useful functions
#f type_str
def type_str(t):
    if t==str:return "string"
    if t==int:return "integer"
    if t==list:return "list"
    if hasattr(t,"__class__"): return str(t.__class__) #.__name__
    return str(t)

#a Exceptions
#c TomlError
class TomlError(Exception):
    def __init__(self, where, reason):
        self.where = where
        self.reason = reason
        pass
    def __str__(self):
        return "%s %s"%(self.where, self.reason)
        pass
    pass

#a Classes
#c TomlDict
class TomlDict(object):
    """
    attributes can be types, or 
    """
    Wildcard = None
    class _values(object):
        def __init__(self, cls, parent):
            self._dict_class = cls
            self._parent = parent
            self._other_attrs = []
            pass
        def Add_other_attr(self, a, v):
            self._other_attrs.append(a)
            setattr(self, a, v)
            pass
        def Get_fixed_attrs(self):
            return self._dict_class._toml_fixed_attrs()
        def Get_other_attrs(self):
            return self._other_attrs
        def Get(self, a):
            return getattr(self, a)
        def Set(self, a, v):
            setattr(self, a, v)
            pass
        def Set_obj_properties(self, o, ks):
            for k in ks:
                v = getattr(self,k)
                if v is not None:
                    setattr(o, k, v)
                    pass
                pass
            pass
        def Iterate(self, callback, descend_hierarchy=True):
            avs = self.Get_attr_dict()
            for (x,value) in avs.items():
                if isinstance(value,TomlDict._values):
                    if descend_hierarchy:
                        values.Iterate(callback)
                    else:
                        callback(self,x,value)
                        pass
                    pass
                else:
                    callback(self,x,value)
                    pass
                pass
            pass
        def Get_attr_dict(self):
            attrs = self.Get_fixed_attrs()
            attrs += self._other_attrs
            r = {}
            for a in attrs:
                r[a] = getattr(self,a)
                pass
            return r
        def Prettyprint(self, prefix=""):
            avs = self.Get_attr_dict()
            for (x,value) in avs.items():
                if isinstance(value,TomlDict._values):
                    value.Prettyprint(prefix = "%s.%s"%(prefix,x))
                    pass
                else:
                    print("%s.%s: %s"%(prefix,x,str(value)))
                    pass
                pass
            pass
        pass
    @classmethod
    def _toml_fixed_attrs(cls):
        attrs = dir(cls)
        v = [x for x in attrs if ((x[0]>='a') and (x[0]<='z'))]
        return v
    def __init__(self, client):
        self.__client = client
        pass

#c TomlDictParser
class TomlDictParser(object):
    """
    """
    @staticmethod
    def identity_fn(s,p,m,x):
        return x
    @staticmethod
    def from_dict_attr_value(t, fn=None):
        if fn==None: fn=TomlDictParser.identity_fn
        def f(self, parent, msg, value):
            if type(value)!=t: raise TomlError(msg, "Expected %s but got '%s'"%(type_str(t),str(value)))
            return fn(self, parent, msg, value)
        return f
    @staticmethod
    def from_dict_attr_list(t, fn=None):
        if fn==None: fn=TomlDictParser.identity_fn
        def f(self, parent, msg, values):
            if type(values)!=list: raise TomlError(msg, "Expected list of %s but got '%s'"%(str(t),str(values)))
            result = []
            for v in values:
                if type(v)!=t: raise TomlError(msg, "Expected %s but got '%s'"%(type_str(t),str(v)))
                result.append(fn(self, parent, msg, v))
                pass
            return result
        return f
    @staticmethod
    def from_dict_attr_dict(t, fn=None):
        """
        t must be a subclass of TomlDict
        """
        if fn==None: fn=TomlDictParser.identity_fn
        def f(self, parent, msg, values):
            if not isinstance(values,dict): raise TomlError(msg, "Expected dictionary but got '%s'"%(str(values)))
            return TomlDictParser.from_dict(t, parent, msg, values)
        return f
    @staticmethod
    def from_dict(cls, handle, msg, d):
        values = cls._values(cls, handle)
        attrs = cls._toml_fixed_attrs()
        rtd = copy.deepcopy(d)
        for x in attrs:
            if x in rtd:
                values_fn = getattr(cls,x)
                setattr(values, x, values_fn(values, handle, "%s.%s"%(msg,x), rtd[x]))
                del(rtd[x])
                pass
            else:
                setattr(values, x, None)
            pass
        if cls.Wildcard is not None:
            for x in rtd:
                v = cls.Wildcard(values, handle, "%s.%s"%(msg,x), rtd[x])
                values.Add_other_attr(x,v)
                pass
            rtd = {}
            pass
        if len(rtd)>0:
            r = []
            for a in rtd.keys(): r.append(a)
            raise TomlError(msg, "Unparsed keys '%s'"%(" ".join(r)))
        return values
    
