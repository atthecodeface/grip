#a Imports
import toml
from .tomldict import TomlDict, TomlDictParser

#a Toml parser classes - description of a .grip/grip.toml file
#c *..TomlDict subclasses to parse toml file contents
class GripConfigTomlDict(TomlDict):
    grip_git_url = TomlDictParser.from_dict_attr_value(str)
    config       = TomlDictParser.from_dict_attr_value(str)
    branch       = TomlDictParser.from_dict_attr_value(str)
    pass

#a Classes
#c GripTomlError - exception used when reading the grip toml file
class GripTomlError(Exception):
    pass

#c GripRepoConfig - complete description of checked-out configuration grip repo, from the config toml file
class GripRepoConfig(object):
    """
    """
    raw_toml_dict = None
    #f __init__
    def __init__(self):
        self.config = None
        self.grip_git_url = None
        self.branch = None
        pass
    #f read_toml_dict
    def read_toml_dict(self, toml_dict):
        self.raw_toml_dict = toml_dict
        values = TomlDictParser.from_dict(GripConfigTomlDict, self, "", self.raw_toml_dict)
        self.build_from_values(values)
        pass
    #f read_toml_file
    def read_toml_file(self, grip_toml_filename):
        try:
            toml_dict = toml.load(grip_toml_filename)
            return self.read_toml_dict(toml_dict)
        except FileNotFoundError:
            pass
        pass
    #f read_toml_string
    def read_toml_string(self, grip_toml_string):
        """
        Really used in test only, read description from string
        """
        return self.read_toml_dict(toml.loads(grip_toml_string))
    #f write_toml_file
    def write_toml_file(self, grip_toml_filename):
        """
        Write the <root_dir>/.grip/config.toml file
        """
        toml_dict = self.toml_dict()
        toml_string = toml.dumps(toml_dict)
        with open(grip_toml_filename,"w") as f:
            f.write(toml_string)
            pass
        pass
    #f build_from_values
    def build_from_values(self, values):
        values.Set_obj_properties(self, {"config", "grip_git_url", "branch"})
        pass
    #f toml_dict
    def toml_dict(self):
        toml_dict = {"config":self.config, "grip_git_url":self.grip_git_url, "branch":self.branch}
        return toml_dict
    #f prettyprint
    def prettyprint(self, acc, pp):
        acc = pp(acc, "repo_config:")
        if self.grip_git_url is not None: acc = pp(acc, "grip_git_url: %s" % (self.grip_git_url), indent=1)
        if self.config       is not None: acc = pp(acc, "config:       %s" % (self.config), indent=1)
        return acc
    #f All done
    pass
