from typing import Dict, Mapping, Optional, List, Any, Tuple, cast

class Toml:
    def __init__(self, **kwargs:Any):
        for (k,v) in kwargs.items():
            setattr(self,k,v)
            pass
        pass
        pass
    def _attrs(self)->List[str]:
        attrs = dir(self)
        return [x for x in attrs if (x[0]!='_')]
    def _as_dict(self) -> Any:
        result = {}
        l = self._attrs()
        for k in l:
            v = getattr(self, k)
            if isinstance(v,Toml):
                result[k] = v._as_dict()
                pass
            else:
                result[k] = v
                pass
            pass
        return result
    def _dict_as_string_list(self, hierarchy:str, d:Dict[str, Any])->List[Tuple[str,str]]:
        result : List[Tuple[str,str]] = []
        hierarchy_contents = ""
        for (k,v) in d.items():
            sub_hierarchy = "%s.%s"%(hierarchy, k)
            if hierarchy == "": sub_hierarchy = k
            if isinstance(v,Toml):
                sub_hierarchy = "%s.%s"%(hierarchy, k)
                result.extend(v._as_string_list(sub_hierarchy))
                pass
            elif type(v)==int:
                hierarchy_contents += "%s = %d\n"%(k,v)
                pass
            elif type(v)==dict:
                result.extend(self._dict_as_string_list(sub_hierarchy,v))
                pass
            elif type(v)==list:
                hierarchy_contents += "%s = ["%k
                iv = cast(List[Any],v)
                comma = ""
                for i in iv:
                    hierarchy_contents += "%s\"%s\""%(comma,str(i))
                    comma = ","
                    pass
                hierarchy_contents += "]\n"
                pass
            else:
                hierarchy_contents += "%s = \"%s\"\n"%(k,str(v))
                pass
            pass

        if hierarchy_contents!="":
            if hierarchy!="":
                hierarchy_contents = "[%s]\n"%(hierarchy)+hierarchy_contents
                pass
            result.append((hierarchy,hierarchy_contents))
            pass
        return result
    def _as_string_list(self, hierarchy:str) -> List[Tuple[str,str]]:
        d = self._as_dict()
        return self._dict_as_string_list(hierarchy=hierarchy, d=d)
    def _as_string(self) -> str:
        sl = self._as_string_list(hierarchy="")
        result = ""
        for (h,s) in sl:
            if h=="": result += "\n"+s
            pass
        for (h,s) in sl:
            if h!="": result += "\n"+s
            pass
        return result
    pass

class ConfigAllToml(Toml):
    repos = ["grip", "cdl", "toolchains", "verilator"]
    doc = """blah"""
    stage = {"download":{"doc":"Download files, particularly for the GCC/binutils toolchain"},
             "configure":{"doc":"Configure all", "requires":["toolchains.configure-riscv32-unknown-elf","verilator.configure","cdl.configure"],},
             "install":{"doc":"Compile and build all the tools", "requires":["toolchains.install-riscv32-unknown-elf","verilator.install","cdl.install"],},
             }
    pass

class GripToml(Toml):
    name = "cdl_tools_grip"
    doc= """Some docu"""
    default_config  = "all"
    configs         = ["all", "test"]
    base_repos :List[str]     = []
    stages          = ["temp", "temp2", "download", "configure","install"]
    workflow        = "readonly"
    env    = Toml(TOOLS_DIR="@GRIP_ROOT_PATH@/tools", PATH="@GRIP_ROOT_PATH@/grip:@TOOLS_DIR@/bin:@PATH@")
    config = Toml(all=ConfigAllToml)

