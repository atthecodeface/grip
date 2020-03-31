# Grip

Grip is a simple tool for managing collections of git modules and submodules,
where the submodules are used in a plethora of higher level modules.

It manages multiple configurations, an supports a test methodology to
provide for continuous integration of multiple higher level modules as
the submodules develop.

## Purpose

Grip is designed to solve the problem in hardware design repository
systems where a class of hardware components (in essence a library)
are developed in one git module and another class are developed in a
second module, and so on. One hardware design may use three different
such hardware libraries, and a different design may use two of these
and a further two different libraries, for example. Both of the
hardware designs are controlled through git, and so use git submodules
for the hardware libraries; as improvements are made, both of the
designs should use the updated libraries.

Furthermore, hardware design tends to depend on tools, which may be in
a further set of respositories. These may be upgraded (in a controlled
fashion) such that hardware designs should be built with new tools,
but it many checkouts of a hardware design a binary set of tools may
be used (instead of requiring, for example, a full GNU toolchain
builds for each hardware checkout).

Hence grip has to manage configurations of git modules, and provide
test mechanisms.

# Grip design

Grip is written in python3 on top of git.

It is designed initially to support a hardware design methodology
where a rust toolchain, gnu binutils, CDL hardware compiler, FPGA
tools, and multiple hardware repositories are used as a top level grip
repository.

# Grip files

Grip configuration is stored in a .grip directory at the root of the
grip repository.

In the .grip repository are the grip configuration file (grip.toml),
the repository state file (state), and other files created and used
during the use of grip (makefiles, environment shell files, etc).

The grip configuration file is user created and edited; it describes
all of the repositories that are part of the grip repository. It is
read by grip, but never updated by it. It is in TOML format, and
should be under version control.

The grip repository state file is also in TOML format. This file
contains the change sets and other changeable state relating to
updates to the repositories. It must be under version control.

Other files are not under version control; these are created and
modified by grip during configuration and operation.

# Grip toml description file

The grip.toml file provides descriptions of the repositories that make
up a grip repository, details on configurations of the grip
repository, and install/build/execution stages that are required by
the grip repository.

A

# Grip modules

A grip modules is simply a git repository. It may have a grip_hooks.py
file somewhere.



# Workflows

A workflow specifies to grip the method for dealing with upstream
repositories, fetching, committing (and changes in general) and for
pushing results.

Currently two workflows are supported - although the aim of grip is to
have a third that is under development.

## "Readonly" workflow

A readonly workflow is used for a git repository that is not meant to
be updated within the grip repository. This may be used, for example,
for a toolchain build setup, or for precompiled tools.

### Cloning

The appropriate branch of the upstream git repository is cloned
locally, and the branch renamed to 'upstream'.

The required commit hash (as specified by the grip state) is checked
out, with a branch name of WIP_<grip_repo_name>

A git repository with a workflow of readonly will never be pushed to.

The changeset of the grip repository must be an ancestor of the head
of the upstream branch; this must always be the case.

If a fetch is performed for a readonly git repository that 
