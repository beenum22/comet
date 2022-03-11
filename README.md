![Release](https://github.com/beenum22/comet/workflows/Release/badge.svg)
![Stable Build](https://github.com/beenum22/comet/workflows/Stable%20Branch/badge.svg?branch=master)
![Default Build](https://github.com/beenum22/comet/workflows/Default%20Branch/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Docker Image Version (latest by date)](https://img.shields.io/docker/v/beenum/comet)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)

# Comet

## Description
Comet is a simple tool to automate/facilitate release cycle that supports single/mono and multi project Git repositories.

Comet performs smart [semantic versioning](https://semver.org/) in an automated release cycle by considering the relevant development changes 
done on the project/s in the target Git repository. It relies on the type of development commits coming in to release 
a smart and sensible version for a project/s. Comet determines the type of change by parsing the commit message that makes
a commit message the essential requirement to provide the smart releases.

By default, Comet supports [conventional commits specification](https://www.conventionalcommits.org/en/v1.0.0/) as the 
commit message strategy. Comet also supports a custom commits strategy where the user has the ability to define 
identifiers for major, minor and patch semantic versioning decisions.

Comet provides support for both [Gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) 
and [Trunk Based Development (TBD)](https://trunkbaseddevelopment.com/) workflow/branching models in the Git repository. 
It also supports an additional custom type where the user defines the branching model strategy/development strategy.

## Installation

Comet can be installed from the source repository using [pip](https://pip.pypa.io/en/stable/) package manager or 
directly use a pre-built Docker image from the [Docker Hub](https://hub.docker.com/repository/docker/beenum/comet).

Execute the following commands to install and use Comet from source repository:
```bash
pip install git+https://github.com/beenum22/comet
comet --version
```

Execute the following commands to use pre-built Comet from the Docker Hub:
```bash
docker run --rm -ti beenum/comet:latest --version
```

## Pre-requisites
* Git repository must follow a defined Git commit messaging strategy that will be used by Comet as a reference point to
  perform smart versioning for the project/s
* Write permissions to the Git repository using the provided credentials or SSH key

## Usage

***Important Note:** Currently, Comet should only be executed from the root directory of any repository*

First, you would need to configure **Comet** in your Git repository. Comet provides a specialized command argument `init` 
to configure the configurations interactively and store them in the default Comet configuration file path `./.comet.yml`. 
Execute the following command to start Comet configuration interactively in your Git repository:

```commandline
comet init
```

Checkout the guidelines provided in [detailed Comet usage](./docs/usage.md#Interactive-Initialization) to understand 
the interactive initialization view and available options.

After Comet initialization, Comet offers multiple workflow scenarios that can be executed for the project/s repository. 
These workflows include **branch specific flow**, **stable version release**, **release candidate creation**, and 
**development and stable branch synchronization**. Checkout the guidelines provided in
[detailed Comet usage](./docs/usage.md#Workflows) to understand and execute different provided workflows in your 
project/s repository. Sample Comet available workflows are provided below: 

```commandline
comet branch-flow
comet release
comet release-candidate
comet sync
```

Comet also supports pushing changes to the remote Git repository using `--push` flag/arugment. However, it is dependent 
on information provided using `--connection-type`, `--ssh-private-key-path` and `--scm-provider` arguments to configure
and push Comet made changes to the remote project/s repository. Checkout the guidelines provided in 
[detailed Comet usage](./docs/usage.md#Push-to-Remote-Repository) to successfully push Comet changes to your remote 
project/s repository.

You can execute the `comet --help` command to print out the general Comet usage:
```bash
comet --help
```

```console
usage: comet [-h] [--version] [--projects] [--project-version PROJECT_VERSION [PROJECT_VERSION ...]] [--project-dev-version PROJECT_DEV_VERSION [PROJECT_DEV_VERSION ...]]
             [--project-stable-version PROJECT_STABLE_VERSION [PROJECT_STABLE_VERSION ...]] [--debug | --suppress]
             [--run {init,branch-flow,release-candidate,release,sync,migrate-config}] [-s SCM_PROVIDER] [-c CONNECTION_TYPE] [-u USERNAME] [-p PASSWORD]
             [-spkp SSH_PRIVATE_KEY_PATH] [-rlp {./}] [-pc PROJECT_CONFIG] [--push]
             [{init,branch-flow,release-candidate,release,sync,migrate-config}]

optional arguments:
  -h, --help            show this help message and exit
  --debug               Enable debug mode
  --suppress            Suppress banner and logging

Versioning:
  Version related operations

  --version             Print Comet version
  --projects            Print all the project names
  --project-version PROJECT_VERSION [PROJECT_VERSION ...]
                        Print project version

Workflow:
  Workflows related operations

  {init,branch-flow,release-candidate,release,sync,migrate-config}
                        Comet action to execute. init: Initialize Comet repository configuration if it does not exist (Interactive mode), branch-flow: Upgrade versioning on
                        Git branches for Comet managed project/s, release-candidate: Create Release candidate branch for Comet managed project/s, release: Release a new
                        version in stable branch for Comet managed project/s, sync: Synchronizes the development branch with stable branch, migrate-config: Upgrades the
                        deprecated Comet configuration format to the newer format
  -s SCM_PROVIDER, --scm-provider SCM_PROVIDER
                        Git SCM provider name
  -c CONNECTION_TYPE, --connection-type CONNECTION_TYPE
                        Git SCM provider remote connection type
  -u USERNAME, --username USERNAME
                        Git username
  -p PASSWORD, --password PASSWORD
                        Git password
  -spkp SSH_PRIVATE_KEY_PATH, --ssh-private-key-path SSH_PRIVATE_KEY_PATH
                        Git SSH local private key path
  -rlp {./}, --repo-local-path {./}
                        Git Repository local path (Support for running Comet for any path other than './' is disabled for now)
  -pc PROJECT_CONFIG, --project-config PROJECT_CONFIG
                        Git Project configuration file path
  --push                Push changes to remote
```

## Newsfeed
### Already using Comet? Make sure you are not using the deprecated configuration
Comet includes major changes related to the configuration file format where multiple configuration parameters have been
replaced or removed. Consult the [configuration migration](./docs/usage.md#Upgrade-Deprecated-Configuration) guide if 
you have already been using Comet in your project repository.

### Do you know CLI commands have been updated? 
Comet has introduced specifying the workflow without the `--run` flag that has been deprecated. For example, now you can 
run the `release` workflow by executing `comet release` instead of `comet --run release`.
One important change in the new CLI method is that `branch-flow` has been replaced by `development` for better 
understanding. For example, `comet --run branch-flow` has been deprecated in favor of `comet development`.
Consult the [configuration migration](./docs/usage.md#Upgrade-Deprecated-Configuration) guide if you have already been 
using Comet in your project repository with the old CLI method.

## Contributing
n/a

## License
[MIT](https://choosealicense.com/licenses/mit/)