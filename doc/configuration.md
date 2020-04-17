# Grip configuration file

The grip configuration file is kept in .grip/grip.toml

It provides basic data to describe the grip repository, and the git
repositories that it consists of. It also provides the different
configurations of the grip repository.

Note that it does not indicate the state of the git subrepositories
required; this is information that changes as the grip repository
develops over time. The grip configuration file need is not modified
over time.

The configuration file consits of global settings, git repository
descriptions, and configuration descriptions.

# Global settings

The global settings for a grip configuration file are:

* name
* doc
* configs
* default_config
* base_repos
* stages
* workflow
* env

## name - string

All grip repositories must have a name, which must consist of
alphanumeric characters and underscores only. (Hence it must match a
regexp of [a-zA-Z0-9_]*.)

## doc - string

This is a documentation string that should describe the grip
repository and its purpose. It is displayed whenever 'grip doc' is
invoked.

doc strings do not undergo environment substitution.

## configs - list of strings

configs contains the list of configurations supported by the grip
repository. For each 'cfg' provided their should be a 'config.<cfg>'
section in the grip configuration file describing the configuration.

The configs list is required as validation against later typos in the
configuration file for configuration section names.

strings in the configs list do not undergo environment substitution.

## stages - list of strings

stages contains the list of stages provided by all of the repository
descriptions in all the configurations in
the repository. Repository descriptions are not permitted to contain a section
describing a stage that uses a name not in the stages list.

The stages list is required as validation against later typos in the
configuration file for repository description stage names.

strings in the stages list do not undergo environment substitution.

## base_repos - list of strings

base_repos defines the repositories that are required by *all*
configurations. This is the fundamental set of repositories required
by the grip repository.

Each <repo_name> in base_repos *must* have a repo.<repo_name>
definition in the grip configuration.

Strings in the base_repos list do not undergo environment substitution.

## workflow - string

The workflow in the global configuration section defines the default
workflow methodology for all the git repositories as well as the
methodlogy for the grip repository itself.

The workflow string does not undergo environment substitution.

## default_config - string

The default_config must specify one of the configurations in the grip
configuration file (hence it must be in the 'configs' list of
strings).

It specifies the configuration to be used for 'grip configure' if a
specific configuration is not supplied.

The default_config string does not undergo environment substitution.

## env - environment description

The global configuration 'env' supplies the basic grip environment
variables for the file. It is a full environment description (see
below) and provides default values that may be overridden in
configuration descriptions or repository descriptions.

The grip global environment has some implicit variables:

* GRIP_ROOT_PATH - the absolute path of the grip repository
* GRIP_ROOT_DIR  - the last directory element of the path of the grip repository
* GRIP_ROOT_URL  - the upstream URL that the grip repository was
  fetched from

The global environment is part of the environment exported in .grip/local.env.sh.

# Grip configuration descriptions

A grip configuration description is the specification of the
environment and repositories required for a particular checkout
configuration of a grip repository. Multiple configurations are
supported in a grip repository to provide, for example, for a
repository which can either build required tools locally or use a
specified path for the tools.

A configuration is specified in a 'config.<cfg_name>' section. This
has the following elements:

* repos
* doc
* env
* repository descriptions

## repos - list of strings

The repos element of a configuration description specifies which git
repositories in addition to the global *base_repos* are required for
the configuration.

Each <repo_name> in repos *must* have a repo.<repo_name>
definition in the grip configuration.

Strings in the repos list do not undergo environment substitution.

## doc - string

The doc element provides documentation for the configuration. It is
displayed when 'grip doc' is invoked: if 'grip doc' is invoked on an
unconfigured grip repository then all of the configurations'
documentation is shown, to provide the user with details on which
configure they might like to select; if 'grip doc' is invoked on a
configured grip repository then the documentation for that
configuration *only* is shown.

doc strings do not undergo environment substitution.

## env - environment description

A specific configuration 'env' supplies the grip environment
variables for the configuration extending the global environment
provided by the global section of the grip configuration file. It is an environment description (see
below) and provides values that may be overridden in
repository descriptions.

The environment is part of the environment exported in .grip/local.env.sh.

## repository descriptions - <repo_name> -> git repository description

Any element in the configuration description that is not one of the
fixed elements is a repository description. The description inherits
from a global repository description of the same name, but it allows
for changes to that description specific to the configuration.

# Git repository description

The git repository descriptions in a grip configuration file describe
the git repositories, where they are to be placed when checked out,
their workflow, and stages of build/execution. The repository
descriptions may be at the top level, using an element name of
repo.<repo_name>, or as part of a configuration (as config.<cfg_name>.<repo_name>)

A repository description contains the following elements:

* url
* branch
* path
* doc
* env
* workflow
* repository stage descriptions

## url - string

This specifies the URL from which to fetch the repository.

url strings may contain environment variables using %<name>% and they
will be substituted with the environment variable value.

## branch - string

This specifies the git branch of the remote URL to fetch from.

branch strings may contain environment variables using %<name>% and they
will be substituted with the environment variable value.

## path - string

This specifies the path (relative to the grip root directory) in which
to clone the git repository.

path strings may contain environment variables using %<name>% and they
will be substituted with the environment variable value.

## doc - string

This is a documentation string that should describe the git
repository, what it contains, why it is included in the grip
configuration, and the stages that it provides. It is displayed whenever 'grip doc' is
invoked for an unconfigured grip repository, and for all repositories in
the configuration of a configured grip repository.

doc strings do not undergo environment substitution

## env - environment description

A repository 'env' supplies the grip environment
variables for the repository extending the configuration environment. It is an environment description (see
below) and provides values that may be overridden in
repository stage descriptions.

Because the environment is a global namespace, repository-specific
environment files should be named appropriately.

The grip repository-local environment has some implicit variables:

* GRIP_REPO_PATH  - the absolute path of the git repository - this
  will be a subdirectory of GRIP_ROOT_PATH

The environment is part of the environment exported in .grip/local.env.sh.

## workflow - string

The workflow in a git repository section defines the workflow
methodology for the git repository, overriding that provided globally
in the global grip configuration section.

The workflow string does not undergo environment substitution.

## repository stage descriptions - <stage_name> -> git repository stage description

The remaining elements of a git repository description describe the
build/execution stages of the git repository. The name must be a stage
name provided in the global *stages* configuration list of strings.

# Git repository stage descriptions

These are for a repo_name.stage_name, either specific to a
configuration or global to the whole grip file. They contain the
following elements:

* requires
* env
* wd
* exec
* >>satisfies

## requires - list of strings (default [])

The *requires* list

## env - environment description

A repository stage description 'env' supplies the grip environment
variables for the repository stage extending the repository environment. It is an environment description (see
below) and provides the final values.

Because the environment is a global namespace, repository-specific
environment files should be named appropriately.

The environment is part of the environment exported in .grip/local.env.sh.

## env


# Example git repository description

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
env = {BUILD_DIR="@GRIP_ROOT_PATH@/build/binutils"}
exec = """ \
mkdir -p ${BUILD_DIR} &&  \
cd ${BUILD_DIR} &&        \
@GRIP_REPO_PATH@/configure --prefix=%RISCV_TOOLS_DIR% --target=riscv64-unknown-elf \
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
url = "binutils.git"
branch = "binutils-2_32-branch"
path = "binutils"
shallow = "true"
env = {BINUTILS_BUILD_DIR="%GRIP_ROOT_PATH%/build/binutils"}

[repo.binutils.configure]
exec = """ \
mkdir -p ${BINUTILS_BUILD_DIR} &&  \
cd ${BINUTILS_BUILD_DIR} &&        \
@GRIP_REPO_PATH@/configure --prefix=%RISCV_TOOLS_DIR% --target=riscv64-unknown-elf \
"""

[repo.binutils.install]
requires = ["binutils.configure"]
wd = "%BINUTILS_BUILD_DIR%"
exec = "make -j8 && make install"
```

## Substitution

The environment variables are substituted for git repository stage
makefile entries (i.e. the env, wd and exec elements).
When substitutions are made for these all %name% are replaced with the
value of name, where the value is taken from the first of:

* the OS environment
* the environment of the repo stage within the configuration
* the environment of the repo description within the configuration
* the environment of the configuration
* the global grip environment

If a name cannot be found in any of these then it is not replaced but
an error is generated.

If the value of a name resolves to a string that includes a %name%
then that name is further resolved.

After all name resolution, all %% pairs resolve to %. An unpaired % is
an error.

Environment variables are also substituted to generate makefile
variables and for a grip environment (retrieved using 'grip env').
The environment that is exported is all of the environment defined by
the repositories in the configuration, the configuration, and the
global grip configuration. The same resolution method is applied as
above, excluding the repo stage (which is not relevant).

