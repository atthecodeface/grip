# Grip configuration file

The grip configuration file is kept in .grip/grip.toml

It provides basic data to describe the grip repository, and the git
repositories that it consists of. It also provides the different
configurations of the grip repository.

Note that it does not indicate the state of the git subrepositories
required; this is information that changes as the grip repository
develops over time. The grip configuration file need is not modified
over time.

The basic concept in a grip configuration file is a git repository
description.

# Git repository description

A git repository used by a grip repository must have a URL to be
sourced from, a branch, and a destination path within the checked-out
grip repository in which to place it.

It should also have a workflow type, although this need not be
specified for each repository individually, as it may use a default
value. (Workflows are the methods of passing updates to git
repositories upstream.)

Additionally the git repository description may include 'stages';
these are the steps that must be performed in using the repository and
their dependencies. For example, a git repository may be the source
for a tool that requires configuration, building and installation
(within th grip repo): these are three stages, each of which is
dependent on the previous stage.

## Example git repository description

```
[config.bld.binutils]
url = "git://sourceware.org/git/binutils-gdb.git"
branch = "binutils-2_32-branch"
path = "binutils"
```

# Environment

It is common to have directories or toolchains referenced more than
once within a makefile, and this is similar within a grip
configuration file. Furthermore, sometimes a configuration stage for a
repository may need to reference paths to tools or repositories, and
these may depend on the actual checkout of a grip repository.

To support some of these requirements a grip configuriation file has
the concept of 'environment'. Firstly, a stage of a repository's
configuration might have a shell script that needs to be executed for
that stage; this shell script can be supplied with an environment such
as 'FRED_DIR=/a/b/c' which is active for just the shell script. The
grip configuration file uses the stage description 'env' key to
provide a dictionary of such values, e.g.:

```
[repo.binutils.configure]
env = {BUILD_DIR="%GRIP_ROOT_PATH%/build/binutils"}
exec = """ \
mkdir -p ${BUILD_DIR} &&  \
cd ${BUILD_DIR} &&        \
%GRIP_REPO_PATH%/configure --prefix=%RISCV_TOOLS_DIR% --target=riscv64-unknown-elf \
"""
```

The 'env'ironment for the shell script will have the variable
'BUILD_DIR' set to /something/build/binutils.

The '%GRIP_ROOT_PATH%' is an invocation of environment substitution
within the grip configuration file. It substitutes the value of the
environment variable GRIP_ROOT_PATH; this variable is actually an
automatic environment variable for the grip repository.

The environments form a hierarchy: a repository description may itself
have an environment, as may a configuration, and as does the whole
grip configuration file. When an environment variable is resolved it
is done at the finest level of granularity possible. An environment
variable may resolve to a value that itself refers to an environment
variable, and this will be resolved as required. The 'GRIP_ROOT_PATH'
automatic variable is in the environment at the topmost of the hierarchy.

An example of the use of the hierarchy is:

```
env             = {RISCV_TOOLS_DIR="%GRIP_ROOT_PATH%/tools/riscv"}

[repo.binutils]
# url = "git://sourceware.org/git/binutils-gdb.git"
url = "binutils.git"
branch = "binutils-2_32-branch"
path = "binutils"
shallow = "true"
env = {BINUTILS_BUILD_DIR="%GRIP_ROOT_PATH%/build/binutils"}

[repo.binutils.configure]
exec = """ \
mkdir -p ${BINUTILS_BUILD_DIR} &&  \
cd ${BINUTILS_BUILD_DIR} &&        \
%GRIP_REPO_PATH%/configure --prefix=%RISCV_TOOLS_DIR% --target=riscv64-unknown-elf \
"""

[repo.binutils.install]
requires = ["binutils.configure"]
wd = "%BINUTILS_BUILD_DIR%"
exec = """ \
 make -j8 &&   \
 make install  \
  """
```
