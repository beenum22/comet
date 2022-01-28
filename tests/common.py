class TestBaseCommitMessages(object):
    BREAKING_FEAT_MSG = """feat(pcscf,cscf_controller): add p-cscf to cscf controller

This change enables the PCSCF to be controlled by the CSCF controller. It also enables the PCSCF to have an extra interface which it then uses to interact with the Packet Core network. This feature adds the following features

* Add MacVLAN / SRIOV interface on P-CSCF
* Remove privileged container in P-CSCF
* Make external network configurable
* Adds resource limits for SRIOV
* Remove headless service creation for P-CSCF
* Remove lifecycle hooks for P-CSCF as it is now managed by CSCF controller

BREAKING CHANGE: If the new controller is not deployed the P-CSCF is not able to be managed by the CSCF controller.
Merges-PR #21
Approved-by: Behnam Hooshiarkashani
Approved-by: Muneeb Ahmad"""

    FEAT_MSG = """feat(srvcc): add a new ansible role srvcc

SUMMARY OF CHANGES:
This PR adds the role SRVCC for automated deployment over a kubernetes cluster. It includes deployment of SRVCC as a CSCF object, required configmaps and services and destruction of these objects upon destroy command

WHAT THIS PR DOES:
It adds an ansible role to deploy SRVCC over a kubernetes cluster
The network design and details of communication can be seen in
https://ng-voice.atlassian.net/wiki/spaces/~575210533/pages/edit-v2/763363350?draftShareId=8c6c444a-848b-4eaa-91cb-eaacf8a61239

WHICH TICKETS THIS PR CATERS FOR
https://ng-voice.atlassian.net/browse/CLD-402

Merges-PR #53
Merged-by: Muhammad Zeeshan
Approved by: Abdul Basit Alvi and Akin Ozer"""

    FIX_MSG = """fix(scscf): add missing jsonrpc configuration for s-cscf

SUMMARY OF CHANGES

Adds missing JSON RPC configuration to S-CSCF configuration.

WHAT THIS PR DOES
This PR adds a bugfix in S-CSCF Kamailio configuration where JSON RPC configuration is missing. After this PR change, `WITH_JSONRPC` is set in the main Kamailio configuration when JSON RPC is enabled using `scscf_jsonrpc` variable.

ADDED VARIABLES
n/a

WHICH ISSUE(S) THIS PR FIXES
https://ng-voice.atlassian.net/browse/CLD-411?atlOrigin=eyJpIjoiYjY4YWI0MDMwNTYwNDU3NDkwMDM2ZWFkOWQ3NzViNDciLCJwIjoiaiJ9

Merges-PR #48
Merged-by: Muneeb Ahmad
Approved-by: Muhammad Zeeshan
Approved-by: Behnam Hooshiarkashani"""

    MERGE_MSG = """Merge in release/2021.1 (pull request #110)

Release/2021.1 merge to develop

Approved-by: Rick Barenthin"""

    CHORE_MSG = """chore: auto update comet config and project version files"""

    INVALID_MSG_1 = """dummy(test): this is an invalid message
No space is provided between title and body
Test body
No space is provided between body and footer
Merged-by: Muneeb Ahmad"""

    INVALID_MSG_2 = """TEST(test)= this is an invalid message
    
Test body
    
Merged-by: Muneeb Ahmad"""

    TEST_DUMMY_COMMITS = {
        "breaking_hash": BREAKING_FEAT_MSG,
        "feat_hash": FEAT_MSG,
        "fix_hash": FIX_MSG,
        "merge_hash": MERGE_MSG,
        "chore_hash": CHORE_MSG
    }


class TestBaseConfig(object):

    TEST_GIT_CONFIG = {
        "username": "dummy",
        "password": "test",
        "ssh_key_path": "~/.ssh/id_rsa",
        "scm_providers": [
            "github",
            "bitbucket"
        ],
        "connection_types": [
            "https",
            "ssh"
        ]
    }

    TEST_DEV_VERSION = "0.1.0-dev.2"
    TEST_STABLE_VERSION = "0.1.0"
    TEST_REPO_DIRECTORY = "test_repo"
    TEST_PROJECT_DIRECTORY_1 = "test_project_1"
    TEST_PROJECT_DIRECTORY_2 = "test_project_2"
    TEST_PROJECT_HISTORY = {
        "next_release_type": "",
        "latest_bump_commit_hash": ""
    }
    TEST_GITFLOW_CONFIG_FILE = ".comet.yml"
    TEST_PROJECT_VERSION_FILE = "VERSION"

    TEST_PROJECT_VERSION_REGEX_ZERO_GROUP = ".*"
    TEST_PROJECT_VERSION_REGEX_ONE_GROUP = "(Version: ).*"
    TEST_PROJECT_VERSION_REGEX_TWO_GROUPS = "(Version)(: ).*"

    TEST_GITFLOW_CONFIGS = {
        "mono": {
            "v0": {
                "strategy": "gitflow",
                "workspace": "beenum22",
                "repo": "comet",
                "stable_branch": "master",
                "development_branch": "develop",
                "release_branch_prefix": "release",
                "projects": [
                    {
                        "path": TEST_REPO_DIRECTORY,
                        "stable_version": TEST_STABLE_VERSION,
                        "dev_version": TEST_DEV_VERSION,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    }
                ]
            },
            "v1": {
                "strategy": "gitflow",
                "workspace": "beenum22",
                "repo": "comet",
                "stable_branch": "master",
                "development_branch": "develop",
                "release_branch_prefix": "release",
                "projects": [
                    {
                        "path": TEST_REPO_DIRECTORY,
                        "version": TEST_DEV_VERSION,
                        "history": TEST_PROJECT_HISTORY,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    }
                ]
            },
            "invalid": {
                "strategy_name": "gitflow",
                "workspace_name": "beenum22",
                "repository": "comet",
                "master_branch": "master",
                "develop_branch": "develop",
                "release_branch_name": "release",
                "projects": [
                    {
                        "name": TEST_REPO_DIRECTORY,
                        "stable_version": TEST_STABLE_VERSION,
                        "dev_version": TEST_DEV_VERSION,
                        "version_regex": "",
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    }
                ]
            }
        },
        "multi": {
            "v0": {
                "strategy": "gitflow",
                "workspace": "beenum22",
                "repo": "comet",
                "stable_branch": "master",
                "development_branch": "develop",
                "release_branch_prefix": "release",
                "projects": [
                    {
                        "path": TEST_REPO_DIRECTORY,
                        "stable_version": TEST_STABLE_VERSION,
                        "dev_version": TEST_DEV_VERSION,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    },
                    {
                        "path": TEST_PROJECT_DIRECTORY_2,
                        "stable_version": TEST_STABLE_VERSION,
                        "dev_version": TEST_DEV_VERSION,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    }
                ]
            },
            "v1": {
                "strategy": "gitflow",
                "workspace": "beenum22",
                "repo": "comet",
                "stable_branch": "master",
                "development_branch": "develop",
                "release_branch_prefix": "release",
                "projects": [
                    {
                        "path": TEST_PROJECT_DIRECTORY_1,
                        "version": TEST_DEV_VERSION,
                        "history": TEST_PROJECT_HISTORY,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    },
                    {
                        "path": TEST_PROJECT_DIRECTORY_2,
                        "version": TEST_DEV_VERSION,
                        "history": TEST_PROJECT_HISTORY,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    }
                ]
            },
            "invalid": {
                "strategy_name": "gitflow",
                "workspace_name": "beenum22",
                "repository": "comet",
                "master_branch": "master",
                "develop_branch": "develop",
                "release_branch_name": "release",
                "projects": [
                    {
                        "name": TEST_REPO_DIRECTORY,
                        "stable_version": TEST_STABLE_VERSION,
                        "dev_version": TEST_DEV_VERSION,
                        "version_regex": "",
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    },
                    {
                        "path": TEST_PROJECT_DIRECTORY_2,
                        "stable_version": TEST_STABLE_VERSION,
                        "dev_version": TEST_DEV_VERSION,
                        "version_regex": TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                        "version_files": [
                            TEST_PROJECT_VERSION_FILE
                        ]
                    }
                ]
            }
        }
    }