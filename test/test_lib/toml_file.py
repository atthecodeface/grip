from typing import Dict, Mapping, Optional, List, Any

class Toml:
    def __init__(self, **kwargs:Any):
        for (k,v) in kwargs:
            setattr(kwargs,k,v)
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

