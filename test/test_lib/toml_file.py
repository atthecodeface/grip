
class TomlThing:
    def __init__(self, **kwargs):
        for (k,v) in kwargs:
            setattr(kwargs,k,v)
            pass
        pass
        pass
    def _attrs(self):
        attrs = dir(self)
        return [x for x in attrs if (x[0]!='_')]
    def _as_dict(self):
        result = {}
        l = self.attrs()
        for k in l:
            v = getattr(self, k)
            if isinstance(v,TomlThing):
                result[k] = v._as_dict()
                pass
            else:
                result[k] = v
                pass
            pass
        return result
    pass

class EnvToml(TomlThing):
    pass
class ConfigAllToml(TomlThing):
    repos = ["grip", "cdl", "toolchains", "verilator"]
    doc = """blah"""
    stage = TomlThing(download=
doc="""Download files, particularly for the GCC/binutils toolchain
This will download tarballs, unpack them, and then download more files as require by gcc prerequisites.
"""

[config.all.stage.configure]
doc="""Configures binutils and gcc for cross-compilation; gcc kinda requires binutils to be installed, so this actually build binutils too"""
requires=["toolchains.configure-riscv32-unknown-elf","verilator.configure","cdl.configure"]

[config.all.stage.install]
doc="""Compile and build all the tools"""
requires=["toolchains.install-riscv32-unknown-elf","verilator.install","cdl.install"]

class GripToml(TomlThing):
    name = "cdl_tools_grip"
    doc= """Some docu"""
    default_config  = "all"
    configs         = ["all", "test"]
    base_repos      = []
    stages          = ["temp", "temp2", "download", "configure","install"]
    workflow        = "readonly"
    env = TomlEnv(TOOLS_DIR="@GRIP_ROOT_PATH@/tools", PATH="@GRIP_ROOT_PATH@/grip:@TOOLS_DIR@/bin:@PATH@")
    config = TomlThing(all=ConfigAllToml)

