# Creating a grip repository

A grip repository is a git repository with the ./grip/grip.toml
configuration file.

## Make the .grip directory

```
mkdir ./grip
```

## Create the grip.toml file

The grip.toml file is the configuration, and so is where the work goes.

In ./grip/grip.toml add:

```
name = "name of grip repository"
doc = """
Documentation of this repository
"""
default_config  = "all"
configs         = ["all"]
base_repos      = []
stages          = []
workflow        = "single"
logging         = "Yes"

[env]

[config.all]
repos = []
doc = """
Documentation 'all' configuration - why it exists
"""

Then add in any repositories required, and put them in to
*base_repos*. For example:

"""
[repo.atcf_hardware_std]
url="https://github.com/atthecodeface/atcf_hardware_std.git"
branch="master"
path="atcf_hardware_std"
"""

Add to *stages* any build/install/run stages that the repos provide
(in their grip.toml files). If the repositories are not grip-aware,
then add to the .grip.toml file descriptions of the stages: for
example, for verilator the cdl_tools_grip repo uses:


[repo.verilator]
url = "https://git.veripool.org/git/verilator"
branch = "stable"
path = "verilator"
doc = """
Verilator is a Verilog/SystemVerilog to C++ compiler. It is not currently used in the CDL hardware,
but it will be.
"""

[repo.verilator.configure]
exec = "unset VERILATOR_ROOT && autoconf && ./configure --prefix=@TOOLS_DIR@"

[repo.verilator.install]
requires = ["verilator.configure"]
exec = "make -j4 && make install"
```

## Initialize the git repo

Initialize the git repo, and the configuration file, and commit

```
git init
git add .grip/grip.toml
git commit -m "[Init] Set up the grip repository" -a
```

## Check the documentation!

The documentation of an unconfigured grip repository is that of the
repository and the possible configurations.

```
grip doc
```

## Configure the grip repository

It is wise to configure with 'verbose' turned on the first time

```
grip configure --verbose
```

This should check out the repositories

## Check the documentation!

The documentation of a configure grip repository is that of the
repository and its configuration, and the repos in the configuration.

```
grip doc
```

## Complete git setup

It is worth adding a .gitignore:

```
echo ".grip/local*" > .gitignore
```

The add the files required:

```
git add .grip/state.toml .gitignore
git commit -m "[configured] Managed first configuration" -a
```

## Use the repository

The repository is ready - a shell is a good start

```
grip shell
```

Then 'grip make', and so on
