[![Default Branch](https://github.com/beenum22/comet/actions/workflows/default-workflow.yml/badge.svg)](https://github.com/beenum22/comet/actions/workflows/default-workflow.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)]

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

**Important Note: Currently, Comet tool should be executed from the root directory of any repository only**

Execute the following `help` command to list down all the available options:
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
  --project-dev-version PROJECT_DEV_VERSION [PROJECT_DEV_VERSION ...]
                        [DEPRECATED] Print development project version
  --project-stable-version PROJECT_STABLE_VERSION [PROJECT_STABLE_VERSION ...]
                        [DEPRECATED] Print stable project version

Workflow:
  Workflows related operations

  {init,branch-flow,release-candidate,release,sync,migrate-config}
                        Comet action to execute. init: Initialize Comet repository configuration if it does not exist (Interactive mode), branch-flow: Upgrade versioning on
                        Git branches for Comet managed project/s, release-candidate: Create Release candidate branch for Comet managed project/s, release: Release a new
                        version in stable branch for Comet managed project/s, sync: Synchronizes the development branch with stable branch, migrate-config: Upgrades the
                        deprecated Comet configuration format to the newer format
  --run {init,branch-flow,release-candidate,release,sync,migrate-config}
                        [DEPRECATED] Comet action to execute. init: Initialize Comet repository configuration if it does not exist (Interactive mode), branch-flow: Upgrade
                        versioning on Git branches for Comet managed project/s, release-candidate: Create Release candidate branch for Comet managed project/s, release:
                        Release a new version in stable branch for Comet managed project/s, sync: Synchronizes the development branch with stable branch, migrate-config:
                        Upgrades the deprecated Comet configuration format to the newer format
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

The main functionality of Comet is triggered using the `--run` flag that supports `init`, `branch-flow`,
`release-candidate` and `release` execution work-flows.

Sample command to initialize Comet for a new project/repository in interactive mode:
```bash
comet --run --init
```

Example command to execute the branch-flow and push changes to the remote/upstream repository
using HTTPs Git connection type:
```bash
comet --run branch-flow --scm-provider bitbucket --connection-type https --username muneeb-ahmad --password dummy --push
```

Example command to execute the branch-flow and push changes to the remote/upstream repository using SSH Git
connection type:
```bash
comet --run branch-flow --scm-provider bitbucket --connection-type ssh --ssh-private-key-path ~/.ssh/id_rsa --push
```

### Demo
In this sample implementation, I will show you how to make use of the Comet versioning utility in your Git project. Comet can be used both locally and in the CI process. In this sample implementation, I will be utilizing Comet in the CI pipelines to demonstrate how it can automate the versioning and release for any project.

We will be setting up Comet for a sample Git repository `dummy` on the Bitbucket Cloud that has been already initialized. This `dummy` repository will contain two sub-projects and the directory structure would look something like this:

```bash
dummy/
├── dummy-1
│       ├── test
│       └── VERSION
├── dummy-2
│       ├── test
│       └── VERSION
├── .git
└── .gitignore
```

Change working directory to the `dummy` repository before executing any of the Comet commands.

```bash
cd dummy
```

Let's initialize the Comet configuration for the repository by executing the following command:
```bash
$ comet init
```

Comet `init` mode initializes the configuration in interactive mode and the following shows the output for the initialization command executed for `dummy` repository:

```log
INFO - Initializing Comet configuration [./.comet.yml] using interactive mode
Select workflow strategy [gitflow]:
Enter the name of the SCM provider workspace/userspace [beenum22]:
Enter the name of the repository[ansible_k8s_ims]: dummy
Enter the name of the stable branch[master]:
Enter the name of the development branch[develop]:
Enter the prefix for release branches[release]:
Do you have sub-projects in the repository?(yes/no)[no]: yes
Enter the path for sub-project: dummy-1
Enter the stable version for sub-project[0.0.0]:
Enter the dev version for sub-project[0.0.0]:
Enter the version regex for sub-project[]:
Include a version file in the sub-project?(yes/no)[no]: yes
Enter the version file path relative to the sub-project?[]: VERSION
Include a version file in the sub-project?(yes/no)[no]: no
Do you have sub-projects in the repository?(yes/no)[no]: yes
Enter the path for sub-project: dummy-2
Enter the stable version for sub-project[0.0.0]:
Enter the dev version for sub-project[0.0.0]:
Enter the version regex for sub-project[]:
Include a version file in the sub-project?(yes/no)[no]: yes
Enter the version file path relative to the sub-project?[]: VERSION
Include a version file in the sub-project?(yes/no)[no]:
Do you have sub-projects in the repository?(yes/no)[no]:
```

## Contributing
n/a

## License
[MIT](https://choosealicense.com/licenses/mit/)