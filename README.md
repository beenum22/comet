# Comet

## Description
Comet is a simple tool to automate/facilitate release cycle.

Comet implements a customized Gitflow-based development work flows for Comet-managed projects. It provides work flows
for branches and new releases. Detailed overview of the work flows is given below:

### Release Flow

### Branch Flow
Branch flows handle how to upgrade the versions and changelogs (Not developed yet) for the target Git branches according to the type of a branch.

   1. Stable branch
   Stable branch flow is executed for a branch specified in `stable_branch` parameter in the Comet configuration file.

   2. Development branch
   Development branch flow is executed for a branch specified in `development_branch` parameter in the Comet configuration file. It uses stable branch version as a reference. If new commits are found on the development branch in comparison to the stable branch, it will bump the development version according to the types of commits found.

   Versions on the development branch have an appended pre-release identifier `dev`.

   For example:
   ```
   Stable version =  1.0.0
   Current Dev version = 1.0.0-dev.1

   One minor change is merged to the development branch.
   New Dev version = 1.1.0-dev.1

   Another minor change is merged.
   New Dev version = 1.1.0-dev.2

   One major change is merged to the development branch.
   New Dev version = 2.0.0-dev.1
   ```
   
   3. Release branch
   Release branch flow is executed for branches with a prefix as specified in `release_branch_prefix` parameter
   in the Comet configuration file. It uses development version as a reference. If new commits are found on the
   release branch in comparison to the development branch, it will look for keywords/identifiers specified for
   version upgrades and only bump the pre-release version.

   Versions on the release branch have an appended pre-release identifier `rc`.

   For example:
   ```
   Dev version =  1.0.0-dev.1
   Current release version = 1.0.0-rc.1

   One patch change is merged to the release branch.
   New release version = 1.0.0-rc.2
   ```

   4. Default branch (Feature/Bugfix/Misc)
   Default branch flow is executed for any branch that doesn't have a dedicated flow. If new commits are found
   in comparison to the development branch, it will upgrade the version by appending a 40 Bytes Hex version for
   latest SHA-1 commit hash as metadata. After the upgrade, it will commit the changes with an optional
   `push_changes` flag that will push changes to the remote if it is set.

   For example:
   ```
   Dev version = 0.1.0-dev.1

   Default branch version =  0.1.0-dev.1+1d1f848c0a59b224206da26fbcae11e0bc5f5190
   ```

## Installation

Comet can be installed from the source repository using [pip](https://pip.pypa.io/en/stable/) package manager or directly use a pre-built Docker image from the [ng-voice Docker registry](dockerhub.ng-voice.com).

Execute the following commands to install and use Comet from source repository:
```bash
pip install git+https://bitbucket.org/ngvoice/comet.git@develop
comet --version
```

Execute the following commands to use pre-built Comet from the Docker registry:
```bash
docker run --rm -ti dockerhub.ng-voice.com/comet:latest --version
```

## Usage

**Important Note: Currently, Comet tool should be executed from the root directory of any repository only**

Execute the following `help` command to list down all the available options:
```bash
comet --help
```

```console
usage: comet [-h] [--version] [--project-dev-version PROJECT_DEV_VERSION [PROJECT_DEV_VERSION ...]] [--project-stable-version PROJECT_STABLE_VERSION [PROJECT_STABLE_VERSION ...]] [--debug | --suppress] [--run {init,branch-flow,release-candidate,release,sync}] [-s SCM_PROVIDER] [-c CONNECTION_TYPE] [-u USERNAME] [-p PASSWORD] [-spkp SSH_PRIVATE_KEY_PATH] [-rlp {./}] [-pc PROJECT_CONFIG] [--push]

optional arguments:
  -h, --help            show this help message and exit
  --debug               Enable debug mode
  --suppress            Suppress banner and logging

Versioning:
  Version related operations

  --version             Print Comet version
  --project-dev-version PROJECT_DEV_VERSION [PROJECT_DEV_VERSION ...]
                        Print development project version
  --project-stable-version PROJECT_STABLE_VERSION [PROJECT_STABLE_VERSION ...]
                        Print stable project version

Workflow:
  Workflows related operations

  --run {init,branch-flow,release-candidate,release,sync}
                        Comet action to execute. [init: Initialize Comet repository configuration if it does not exist (Interactive mode), branch-flow: Upgrade versioning on Git branches for Comet managed project/s, release-candidate: Create Release candidate branch for Comet managed project/s], release: Release a new version in stable branch for Comet managed project/s], sync: Synchronizes the development branch with stable branch
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
$ comet --run init
```

Comet `init` mode initializes the configuration in interactive mode and the following shows the output for the initialization command executed for `dummy` repository:

```log
INFO - Initializing Comet configuration [./.comet.yml] using interactive mode
Select workflow strategy [gitflow]:
Enter the name of the SCM provider workspace/userspace [ngvoice]:
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

Since we want to automate the versioning through the CI pipelines, we will configure Bitbucket CI configuration file to implement Comet versioning flows. Before proceeding to configure the Bitbucket pipelines CI, make sure to add Bitbucket and Docker credentials as environment variables in Bitbucket CI section. In this demo, we'll be using the following variables:
* BITBUCKET_USERNAME
* BITBUCKET_APP_PASSWORD
* DOCKER_HUB_USERNAME
* DOCKER_HUB_PASSWORD

Now we can proceed to configure the Bitbucket CI configurations. Add the following configurations for this demo to set up pipelines for version upgrade and automated releases:
```yaml
image: atlassian/default-image:2

options:
  docker: true

definitions:
  steps:

    - step: &push-comet-upgrades
        name: Push Comet Upgrades
        clone:
          depth: full
        script:
          - git log
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - git push origin

    - step: &release
        name: Release version
        image:
          name: dockerhub.ng-voice.com/comet:0.2.0-dev.9
          username: $DOCKER_HUB_USERNAME
          password: $DOCKER_HUB_PASSWORD
        clone:
          depth: full
        script:
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - >-
            comet
            --debug
            --run release
            --username ${BITBUCKET_USERNAME}
            --password ${BITBUCKET_APP_PASSWORD}
            --connection-type https
            --push

    - step: &upgrade-version
        name: Upgrade Version
        image:
          name: dockerhub.ng-voice.com/comet:0.2.0-dev.9
          username: $DOCKER_HUB_USERNAME
          password: $DOCKER_HUB_PASSWORD
        clone:
          depth: full
        script:
          - git remote set-url origin https://${BITBUCKET_USERNAME}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/${BITBUCKET_WORKSPACE}/${BITBUCKET_REPO_SLUG}
          - git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
          - git fetch origin
          - >-
            comet
            --debug
            --run branch-flow
            --username ${BITBUCKET_USERNAME}
            --password ${BITBUCKET_APP_PASSWORD}
            --connection-type https

    - step: &build-dummy-1
        name: Build dummy 1
        condition:
          changesets:
            includePaths:
              - "dummy-1/**"
        script:
          - echo "Dummy 1 demo"
          
    - step: &build-dummy-2
        name: Build dummy 2
        condition:
          changesets:
            includePaths:
              - "dummy-2/**"
        script:
          - echo "Dummy 2 demo"

pipelines:
  custom:
    release:
      - step: *release

  default:
    - step:
        <<: *upgrade-version
        name: Generate Comet Config
        artifacts:
          - "**"
          - ".**"
    - parallel:
      - step: *build-dummy-1
      - step: *build-dummy-2
    - step: *push-comet-upgrades
```

## Contributing
n/a

## License
[MIT](https://choosealicense.com/licenses/mit/)