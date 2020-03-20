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

# Checkout / configuration commands

## grip configure

This command configures a grip repository to one of the configurations
specified in the .grip/grip.toml file. It clones the git repositories
required by that configuration, and updated local files to match. Once
a grip repoistory has been configured, it cannot be reconfigured.

## grip clone

This is a convenience function to perform a git clone followed by a
grip configure

