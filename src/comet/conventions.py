from typing import List, Dict
import logging
import re
from .semver import SemVer

logger = logging.getLogger(__name__)


class ConventionalCommits(object):

    COMMIT_TYPES: Dict[str, Dict[str, str]] = {
        "ci": {
            "description": "Adds changes to CI configuration files and scripts",
            "example": "ci(bitbucket): upgrade helm charts deployment for staging env"
        },
        "feat": {
            "description": "Adds a new minor feature that is backwards compatible",
            "example": "feat(pcscf): add support for macvlan in p-cscf"
        },
        "fix": {
            "description": "Adds a bug-fix or a hot-fix",
            "example": "fix(powerdns): fix domains configuration in powerdns recursor"
        },
        "docs": {
            "description": "Adds changes to the documentation",
            "example": "docs(k8s): add readme for kubernetes deployment playbook"
        },
        "refactor": {
            "description": "Adds changes to the code/main app that neither adds a feature or a fix",
            "example": "refactor(multus): move multus templates to rke directory"
        },
        "perf": {
            "description": "Adds changes for performance improvement",
            "example": "perf(powerdns): remove redundant file reads for domain configurations"
        },
        "test": {
            "description": "Adds changes for new or existing test-cases",
            "example": "test(pcscf): upgrade molecule to use kind k8s utility"
        },
        "build": {
            "description": "Adds changes that affect the build system or external dependencies",
            "example": "build(docker): add docker daemon configuration for ci env"
        },
        "style": {
            "description": "Adds changes that do not affect the main app such as formatting, etc",
            "example": "style(rke): add comments to the rke deployment scripts"
        },
        "chore": {
            "description": "Adds changes that do not affect the app source files such branch syncs, version bumps, etc",
            "example": "chore(ims): sync develop branch with stable branch"
        },
        "revert": {
            "description": "Reverts changes",
            "example": "revert(pcscf): revert macvlan support from p-cscf"
        },
        "release": {
            "description": "Reverts changes",
            "example": "revert(pcscf): revert macvlan support from p-cscf"
        },
        "merge": {
            "description": "Reverts changes",
            "example": "revert(pcscf): revert macvlan support from p-cscf"
        }
    }

    DEFAULT_VERSION_COMMIT: str = "chore: auto update comet config and project version files\n\n[skip ci]"

    # Motivation from:
    # https://github.com/commitizen-tools/commitizen/blob/aa0debe9ae5939afb54de5f26c7f0c395894e330/commitizen/defaults.py#L45
    COMMIT_SEMVER_REGEX: str = r"^(?P<change_type>feat|fix|refactor|perf)" \
                               r"(?P<breaking_sign>!)?(?:\((?P<scope>[^()\r\n]*)\)|\()?:\s(?P<summary>.*)" \
                               r"\n?\n?(?P<body>[\s\S]*\n\n)?\n?(?P<breaking_footer>BREAKING CHANGE)?" \
                               r"(?P<footers>[\s\S]*)"
    COMMIT_PARSER_REGEX: str = fr"^(?P<change_type>{'|'.join(list(COMMIT_TYPES.keys()))})" \
                               fr"(?P<breaking_sign>!)?(?:\((?P<scope>[^()\r\n]*)\)|\()?:\s(?P<summary>.*)" \
                               fr"\n?\n?(?P<body>[\s\S]*\n\n)?\n?(?P<footers>[\s\S]*)"
    # IGNORED_COMMIT_REGEX: str = r"^((Merge pull request)|(Merge (.*?) into (.*?)|(Merge branch (.*?)))(?:\r?\n)*$)"
    IGNORED_COMMIT_REGEX: List[str] = [
        r"^((Merge pull request)|(Merge (.*?) into (.*?)|(Merge branch (.*?)))(?:\r?\n)*$)",
        r"chore: auto update comet config and project version files"
    ]
    SEMVER_BUMP_KEYWORDS: Dict[str, List[str]] = {
        SemVer.MAJOR: [
            "feat!",
            "BREAKING CHANGE"
        ],
        SemVer.MINOR: [
            "feat"
        ],
        SemVer.PATCH:  [
            "fix",
            "refactor",
            "perf"
        ]
    }

    @staticmethod
    def lint_commit(commit_msg: str) -> bool:
        if re.search(ConventionalCommits.COMMIT_PARSER_REGEX, commit_msg):
            logger.debug(f"Commit message [{commit_msg}] follows the Conventional Commits Spec")
            return True
        return False

    @staticmethod
    def ignored_commit(commit_msg: str) -> bool:
        for pattern in ConventionalCommits.IGNORED_COMMIT_REGEX:
            if re.search(pattern, commit_msg):
                logger.debug(f"Commit message [{commit_msg}] should be ignored")
                return True
        return False

    @staticmethod
    def get_bump_type(commit_msg: str) -> str:
        try:
            bump = SemVer.NO_CHANGE
            assert ConventionalCommits.lint_commit(
                commit_msg), "Conventional Commits linting failed. Please verify that the commit formatting " \
                             "complies with Conventional Commits specification"
            logger.debug(f"Parsing Conventional Commits format commit message[{commit_msg}]")
            parsed_commit = re.search(ConventionalCommits.COMMIT_SEMVER_REGEX, commit_msg)
            if parsed_commit:
                commit_type = parsed_commit.groupdict()['change_type']
                commit_breaking_sign = parsed_commit.groupdict()['breaking_sign']
                commit_breaking_footer = parsed_commit.groupdict()['breaking_footer']
                for bump_type in list(ConventionalCommits.SEMVER_BUMP_KEYWORDS.keys()):
                    if commit_type + (commit_breaking_sign if commit_breaking_sign else "") in ConventionalCommits.SEMVER_BUMP_KEYWORDS[bump_type] or commit_breaking_footer:
                        logger.debug(f"Conventional Commits format commit message matches '{bump_type}' version bump")
                        bump = bump_type
                        return bump
            return bump
        except AssertionError as err:
            logger.debug(f"Conventional Commits parsing failed for commit message: [{commit_msg}]")
            raise
