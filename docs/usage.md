# User Guide
## Supported Development Models
### Gitflow
### Trunk-based Development (TBD)

## Supported Commit Message Strategies
### Conventional Commits
Comet includes an implementation of [conventional commits specification](https://www.conventionalcommits.org/en/v1.0.0/) 
that has a defined process to parse the commit messages and take versioning decisions based on the type of commits. 
In semantic versioning, we have three main types of versions; `major`, `minor` and `patch`. Comet has defined rules 
to map the type of commit messages with the type of versioning decision to take. Mapping between the semantic versioning 
and the conventional commits specification is given below:

* `feat!` type or `BREAKING CHANGE` identifier in the commit message would be considered a *Major* change.
* `feat` type commit message would be considered a *Minor* change.
* `fix`, `refactor` and `perf` types commit messages would be considered a *Patch* change.

This commit message strategy is the default strategy used by the Comet and is currently the only supported in Comet.

## Configuration Reference
### `strategy`
Specifies all the strategic decisions in Comet. This parameter is intended to contain all the current/future 
automated release strategies.
#### `commits_format`
Specifies all the information related to commit messaging format/strategy used in the project/s repository.
##### `type`
Specifies the type of commit messaging format to use for automated release. Currently, Conventional Commits Specification 
is supported only by setting it to `conventional_commits`. Future releases would include a user defined commit 
messaging format by setting it to `custom`.
##### `options`
Specifies additional configuration required for the type of commit messaging format selected. `conventional_commits` 
doesn't require any additional options and `options` field can be ignored for it.
#### `development_model`
Specifies all the information related to development/branching model configured for the project/s repository.
##### `type`
Specifies the type of development/branching model to use for automated release. Currently, Gitflow-based and Trunk-based 
Development (TBD) development models are supported by setting it to `gitflow` and `tbd` respectively. Future releases 
would include a user defined development model/workflow by setting it to `custom`.
##### `options`
Specifies additional configuration required for the type of development/branching model selected. `gitflow` requires
stable and development branches' names by setting `stable_branch` and `development_branch` fields. `gitflow` also 
requires prefix for release candidate branches by setting `release_branch_prefix`. `tbd` doesn't require any additional 
options and `options` field can be ignored for it.
### `workspace`
Specifies the Git username/workspace name where the repository with target project/s is present. 
### `repo`
Specifies the Git repository name where the target project/s for automated release are present.
### `projects`
Specifies a list of mappings with all the target project/s present in the Git repository that requires automated 
release.
#### `version`
Specifies the current/latest version for the project.
#### `history`
Specifies the historic information related to project versioning.
##### `next_release_type`
Specifies the next possible stable release type according to semantic versioning. This field is only intended to be 
used by the Comet tool itself. **Do not modify**.
##### `latest_bump_commit_hash`
Specifies the commit hash for the last version-able change impacting the major, minor or patch parts in a semantic 
version. This field is only intended to be used by the Comet tool itself. **Do not modify**.
#### `version_files`
Specifies a list of version file/s where the version string needs to be updated.
#### `version_regex`
Specifies the regular expression pattern to lookup for version strings in the specified version file/s and replace 
them. If left empty, it will look for the exact past version and replace it with the new version in the specified 
version file/s. `version_regex` is a specialized field and can be used in complicated scenarios where the version strings 
in version file/s cannot be updated by simply replacing past version or matching any semantic version with a new version 
A regular expression can be specified here to lookup for version string patterns and replace them with a new version. 
However there is a caveat to that, if the user needs to find the areas using regex capturing groups after which the 
version string must be updated then this field has a limitation of only one regex capturing group.

For example, if we have the following value set:
```yaml
version_regex: '(Version: ).*'
```
Let's assume our new version is `1.1.1`. This regular expression would look for all strings in a line after `Version: ` 
string in version file/s and replace it with `Version: 1.1.1`. The regex capturing group should only be used in case 
when version string lookup will not be enough due to multiple instances of version strings in the target version files. 

If the user provides two capturing groups, for example `(Version: )(Test).*`, Comet will throw an error.

## Usage

## Interactive Initialization
Comet provides an interactive mode to configure your project/s repository with Comet configuration. This step is a 
pre-requisite to all the Comet provided operations. To manage automated release cycle in your repository using **Comet**,
Trigger the initialization by executing the following at the root path in your project/s repository:
```commandline
comet init
```

User will be prompted with an interactive mode to configure/provide all the relevant information required by the Comet. 
After successfully initializing Comet in your project/s repository, a configuration file, `./.comet.yml`, would be added 
on the root path of your repository. This configuration will be used by Comet in future as reference configuration file 
and to keep track of all release changes. 

## Available Workflows

***Warning:** Some supported workflows are dependent on specific branching models.*
### Gitflow (`gitflow`)
#### Release (`release`)
This workflow is intended to release a stable version for the project/s in user repository according to the Gitflow 
model. Comet releases a new version on the stable branch for the projects that has development changes on the 
development branch. A new Git tag is also push to the stable branch for each newly released project version. No version 
is released if there are no changes found on the development branch with respect to the stable branch for any of the 
configured project.

Sample:
```commandline
comet release
```

#### Development Flow (`developemnt`)
This workflow is intended to upgrade the version after changes on the main development branch, stable branch, release 
candidate branches or any other feature/user branches. On the development branch, this workflow computes the next 
possible stable version intelligently by the parsing messages of the new development commits with respect to the stable 
branch. On the release candidate branches, it simply increments the build number for the version. For rest of the user 
branches including the feature branches, this workflow upgrades the version with an appended last commit hash. Lastly, 
on the stable branch, only patch changes are allowed resulting in only patch upgrades.

Sample:
```commandline
comet development
```

#### Release Candidate (`release-candidate`)
This workflow is intended to create release candidate branches for the project/s with new changes on the development 
branch with respect to the stable branch. A new release candidate branch is added with a prefix according to the value 
configured in `release_branch_prefix` parameter in the Gitflow options.

Sample:
```commandline
comet release-candidate
```

***Note:** This workflow is currently not supported on the repository with multi projects*

#### Branch Synchronization (`sync`)
This workflow is intended to synchronization the stable and development branches and is only supported for the 
Gitflow-based model.

Sample:
```commandline
comet sync
```

### Trunk-based Development (`tbd`)
***Warning:** In progress*

#### Stable Release (`release`)
#### Development Version (`developemnt`)
#### Release Candidate (`release-candidate`)
#### Stable and Development Branches Synchronization (`sync`)

## Push to Remote Repository
Comet supports pushing all the changes to the remote project/s repository using a `--push` flag. To successfully make 
changes in the remote repository, it requires the name of Source Code Management (SCM) provider, Git connection type, and 
SSH private key local file path or username and password depending on the type Git connection type specified. This 
information is used to compute remote repository URL and verify connectivity to the SCM provider using the computed 
URL and provided credentials. The required Comet arguments are `--connection-type`, `--ssh-private-key-path`, 
`--username`, `--password` and `--scm-provider`.

Sample Comet commands to execute any workflow and push changes to the remote repository using 
SSH and HTTPS Git connection types are provided below in order:
```commandline
comet release --scm-provider github --connection-type ssh --ssh-private-key-path ~/.ssh/id_rsa --push
```
```commandline
comet release --scm-provider github --connection-type https --username dummy --password dummy --push
```

## Upgrade Deprecated Configuration
Some major changes/improvements has been made in the configuration parameters format resulting in deprecation of some 
configuration parameters. The changes include refactoring the versioning related parameters, and replacing `dev_version`
and `stable_version` parameters with newer `version` and `history` parameters. The new `history` parameter is included 
to keep track of the version changes and has additional `next_release_type` and `latest_bump_commit_hash` parameters to 
facilitate the automated smart versioning of the project/s in your repository. 

Additionally, the `strategy` parameter has been converted into a mapping that will contain all the strategy/design 
related parameters. For this reason, `development_branch`, `stable_branch` and `release_branch_prefix` parameters 
required by the Gitflow branching model are moved to the newer `strategy` mapping.

Comet provides a command to migrate the deprecated configuration format to the newer format without any manual user 
intervention. You can execute the following to migrate your configuration:
```commandline
comet migrate-config
```