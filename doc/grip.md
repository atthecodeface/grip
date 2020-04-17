# 'grip'

'grip' operates in a similar way to git - it expects a command. The
commands supported by grip can be found using 'grip commands'.

# Basic commands

## grip help

This returns the help for a grip command: e.g. 'grip help root' will
describe the 'grip root' command.

# Interrogation commands

## grip root

Within a grip repository, 'grip root' will return the absolute path to
the grip repository root directory, where the '.grip' configuration
directory resides.

If not within a grip repository, and error will be returned.

A pathname may be supplied to 'grip root'; in this case the grip
repository root directory of that path will be returned.

## grip env

This command returns a shell-style environment (suitable for sh, bash,
etc) that is defined by the configuration of the grip repository. This
includes two grip-defined variables:

* GRIP_ROOT_PATH, which is the path to the root of the grip repository
in the files system
* GRIP_ROOT_URL, which is the URL from which the grip repository was cloned

# Shell commands
## grip shell

grip shell invokes a BASH shell with the environment set based on the
configuration.

Particularly the following environment variables are defined by grip
itself:

* GRIP_SHELL - not an empty string
* GRIP_ROOT_URL - URL to the git repo of the grip repository
* GRIP_ROOT_PATH - absolute pathname of the git repo of the grip repository
* GRIP_ROOT_DIR - last path element of GRIP_ROOT_PATH

If the grip configuration specifies a PATH, then this shell will (of
course) have that path. Hence it is very useful for invoking a
subshell in which to execute repository-related commands

A .bashrc which utilizes these variables for a prompt might be:

```
PS1_head="\a\e[0;36m\t:\!"
PS1_middle=""
PS1_tail="\e[0;36m:\w$\e[m\n$ "
if [ "z$GRIP_SHELL" != "z" ]
then
  PS1_middle=":\e[0;32mgrip:$GRIP_REPO"
fi
PS1="$PS1_head$PS1_middle$PS1_tail"
```

# Checkout / configuration commands

## grip configure

This command configures a grip repository to one of the configurations
specified in the .grip/grip.toml file. It clones the git repositories
required by that configuration, and updated local files to match. Once
a grip repoistory has been configured, it cannot be reconfigured.

## grip clone

This is a convenience function to perform a git clone followed by a
grip configure

