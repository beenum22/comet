# Usage
## Interactive Initialization
## Workflows
***Warning:** Some supported workflows are dependent on specific branching models.*

## Push to Remote Repository

## Upgrade Deprecated Configuration
Some major changes/improvements has been made in the configuration parameters format resulting in deprecation of the 
old configuration format. The changes include refactoring the versioning related parameters, and replacing `dev_version`
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