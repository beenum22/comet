# from typing import TypedDict, List, Dict
import logging
import os
from .scm import Scm
from .semver import SemVer
from .conventions import ConventionalCommits
from .config import ConfigParser
from .utilities import CometUtilities, CometDeprecationContext

logger = logging.getLogger(__name__)


class WorkflowBase(object):
    """Backend to handle Gitflow based development work flows.

    This GitFlow backend implements customized Gitflow-based development work flows for Comet-managed projects. The
    GitFlow object provides work flows for branches and releases. Detailed overview of the work flows is given below:

    Branch Flows:
        Branch flows handle how to upgrade the versions and changelogs (Not developed yet) for the target Git
        branches according to the type of a branch.

        1. Stable branch
           Underdevelopment

        2. Development branch
           Development branch flow is executed for a branch specified in :ivar:`development_branch` parameter. It uses
           stable branch version as a reference. If new commits are found on the development branch in comparison to
           the stable branch, it will bump the development version according to the types of commits found. Versions
           bumps are performed for the keywords/identifiers found specified in the `ConventionalCommits` class.

           Versions on the development branch have an appended pre-release identifier `dev`.

           For example:

           Stable version =  1.0.0

           Current Dev version = 1.0.0-dev.1

           One minor change is merged to the development branch.

           New Dev version = 1.1.0-dev.1

           Another minor change is merged.

           New Dev version = 1.1.0-dev.2

           One major change is merged to the development branch.

           New Dev version = 2.0.0-dev.1

        3. Release branch
           Release branch flow is executed for branches with a prefix as specified in `release_branch_prefix` parameter
           in the Comet configuration file. It uses development version as a reference. If new commits are found on the
           release branch in comparison to the development branch, it will look for keywords/identifiers specified in
           the `ConventionalCommits` class for version upgrades and only bump the pre-release version.

           Versions on the release branch have an appended pre-release identifier `rc`.

           For example:

           Dev version =  1.0.0-dev.1

           Current release version = 1.0.0-rc.1

           One patch change is merged to the release branch.

           New release version = 1.0.0-rc.2

        4. Default branch (Feature/Bugfix/Misc)
           Default branch flow is executed for any branch that doesn't have a dedicated flow. If new commits are found
           in comparison to the development branch, it will upgrade the version by appending a 40 Bytes Hex version for
           latest SHA-1 commit hash as metadata. After the upgrade, it will commit the changes with an optional
           :ivar:`push_changes` flag that will push changes to the remote if it is set.

           For example:

           Dev version = 0.1.0-dev.1

           Default branch version =  0.1.0-dev.1+1d1f848c0a59b224206da26fbcae11e0bc5f5190

    Release Flows:
        1. Release Candidate branch
        2. Release to Stable branch


    handle how to upgrade the versions and changelogs (Not developed yet) for the target Git
    branches according to the type of a branch.

     . The idea is
    to have a class that handles all the Semantic Versioning related operations for the requested project. This class
    depends on `ConfigParser` class and is only supposed to be used with Comet too. It can be used with other tools if
    they follow the Comet philosophy or design.

    The SemVer object can read the reference version in the main project version file (.comet.yml usually), bump it
    according to the requested type of version bump and update the main project version file. Since, it depends on
    the Comet design, it can use two types of reference versions: `dev` and `stable`.
    This SemVer object also supports updating project specific version file paths using the provided regex pattern.

    .. important::
        Semver instance represents one project version only.

    Example:

    .. code-block:: python

        gitflow = GitFlow(
            connection_type="https",
            scm_provider="bitbucket",
            username="dummy",
            password="test",
            ssh_private_key_path="~/.ssh/id_rsa",
            project_local_path="./",
            project_config_path=".comet.yml",
            push_changes=False
        )

        gitflow.default_branch_flow()

    """

    def __init__(
            self,
            connection_type: str = "https",
            scm_provider: str = "bitbucket",
            username: str = "",
            password: str = "",
            ssh_private_key_path: str = "~/.ssh/id_rsa",
            project_local_path: str = "./",
            project_config_path: str = "./comet",
            push_changes: bool = False
    ) -> None:
        """
        Initializes a GitFlow object.

        :ivar connection_type: Git connection type for SCM provider
        :ivar scm_provider: Source Code Management Provider name
        :ivar username: Git username with write access to the project/repository
        :ivar password: Git user password with write access to the project/repository
        :ivar ssh_private_key_path: SSH private key file path on the local machine with write access to the project/repository
        :ivar project_config_path: Comet configuration file
        :ivar project_local_path: Local repository directory path
        :ivar push_changes: Optional flag to push changes to remote/upstream repository
        :return: None
        :raises Exception:
            raises an exception if it fails to execute work flow preparation steps
        """
        self.connection_type = connection_type
        self.scm_provider = scm_provider
        self.username = username
        self.password = password
        self.ssh_private_key_path = ssh_private_key_path
        self.project_config_path = project_config_path
        self.project_local_path = project_local_path
        self.push_changes = push_changes
        self.scm = None
        self.project_config = None
        self.projects_semver_objects = {}
        self.prepare_workflow()

    def _sanitize_paths(self) -> None:
        """
        Sanitizes/normalizes local project path with Comet configuration file at its root.

        :return: None
        """
        logger.debug(f"Sanitizing paths according to the root/repo directory [{self.project_local_path}]")
        self.project_local_path = os.path.normpath(f"{self.project_local_path}")
        self.project_config_path = os.path.normpath(f"{self.project_local_path}/{self.project_config_path}")
        logger.debug(f"Sanitized paths according to the root/repo directory [{self.project_local_path}]")

    @CometUtilities.deprecation_facilitation_warning
    def _set_deprecated_version_type(self, version_type: str) -> [str, None]:
        """
        Sets the reference version type according to :param:`version_type` for the specified project if the
        deprecated versioning format is configured where 'dev_version' and 'stable_version' parameters are
        configured for a Comet-managed project.

        :param version_type:
            Reference version type to set if deprecated versioning format is configured in the
            Comet configuration file
        :return:
            Reference version type if the deprecated versioning format is configured or 'None' otherwise
        """
        if self.project_config.has_deprecated_versioning_format():
            return version_type
        return None

    def prepare_workflow(self) -> None:
        """
        Executes workflow preparation steps by parsing configuration file and initiailizing Scm instance.

        :return: None
        :raises Exception:
            raises an exception if it fails to parse the config file or initialize the Scm instance
        """
        try:
            self._sanitize_paths()
            self.project_config = ConfigParser(
                config_path=self.project_config_path
            )
            self.project_config.read_config(sanitize=True, validate=True)

            self.scm = Scm(
                scm_provider=self.scm_provider,
                connection_type=self.connection_type,
                username=self.username,
                password=self.password,
                repo=self.project_config.config["repo"],
                workspace=self.project_config.config["workspace"],
                repo_local_path=self.project_local_path,
                ssh_private_key_path=self.ssh_private_key_path
            )
        except Exception:
            raise

    # TODO: Remove redundant commented out lines
    @CometUtilities.deprecated_arguments_warning("reference_version_type")
    def prepare_versioning(self, reference_version_type: str = "") -> None:
        """
        Prepares project/s specific SemVer instances according to the reference version type specified in
        :var:`reference_version_type`.

        :param reference_version_type: Reference version type (Deprecated)
        :return: None
        :raises Exception:
            raises an exception if it fails to initialize version for any of the projects
        """
        try:
            for project in self.project_config.config["projects"]:
                self.projects_semver_objects[project["path"]] = SemVer(
                    project_path=project["path"],
                    version_files=project["version_files"],
                    version_regex=project["version_regex"],
                    project_version_file=self.project_config_path,
                    reference_version_type=reference_version_type
                )
        except Exception:
            raise

    @CometUtilities.unstable_function_warning
    def bump_project_version(
            self,
            project: str,
            commits: list,
            pre_release_str: [str, None] = None,
            pre_release_only: bool = False,
            build_only: bool = False,
            check_history: bool = True,
    ) -> int:
        """Bump the project version.

        Execute version bumps for the project based on the type of commits provided.

        :param project: Target project path
        :param commits: List of commit hashes to parse
        :param pre_release_str: Optional pre_release identifier to set. Default: None
        :param pre_release_only: Optional flag to only bump the pre-release version part. Default: False
        :param build_only: Optional flag to only bump the build version part. Default: False
        :param check_history:
            Optional flag to bump versions dynamically with considering version history. Default: True
        :return: Latest version bump type
        """
        past_bump = SemVer.NO_CHANGE
        if not self.project_config.has_deprecated_versioning_format():
            past_bump = self.projects_semver_objects[project].get_version_enum_value(
                self.project_config.get_project_history(project)["next_release_type"]
            )
        current_bump = SemVer.NO_CHANGE
        next_bump = SemVer.NO_CHANGE

        if self.project_config.has_deprecated_versioning_format() and pre_release_only:
            with CometDeprecationContext(
                    f"Pre-release only version bump is requested for the deprecated project versioning logic that "
                    f"uses 'dev_version' and 'stable_version' parameters. Pre-release only version bumps require "
                    f"'history parameter in Comet configuration. Resetting pre-release version part to handle "
                    f"deprecated project versioning (x.y.z-rc.1)"
            ):
                self.projects_semver_objects[project].reset_version_pre_release()

        if build_only:
            new_version_hex = self.scm.get_commit_hexsha(commits[-1], short=True)
            self.projects_semver_objects[project].bump_version(
                release=SemVer.BUILD,
                pre_release=pre_release_str,
                build_metadata=f"{new_version_hex}",
                static_build_metadata=True
            )
            return past_bump

        for commit in commits:
            bump_type = ConventionalCommits.get_bump_type(
                self.scm.get_commit_message(commit)
            )
            logger.debug(
                f"Current Version: {self.projects_semver_objects[project].get_version()}, "
                f"Past Bump: {SemVer.SUPPORTED_RELEASE_TYPES[past_bump]}, "
                f"Current Bump: {SemVer.SUPPORTED_RELEASE_TYPES[current_bump]}, "
                f"Next Bump: {SemVer.SUPPORTED_RELEASE_TYPES[next_bump]}"
            )
            if bump_type == SemVer.NO_CHANGE:
                continue
            if pre_release_only:
                next_bump = SemVer.PRE_RELEASE
                self.projects_semver_objects[project].bump_version(
                    release=next_bump, pre_release=pre_release_str
                )
            elif check_history:
                next_bump = bump_type
                current_bump = self.projects_semver_objects[project].compare_bumps(past_bump, next_bump)
                self.projects_semver_objects[project].bump_version(
                    release=current_bump, pre_release=pre_release_str)
                if current_bump == SemVer.PRE_RELEASE and past_bump > next_bump:
                    continue
                else:
                    past_bump = next_bump
            else:
                next_bump = bump_type
                self.projects_semver_objects[project].bump_version(
                    release=next_bump, pre_release=pre_release_str)
                past_bump = next_bump
        return past_bump

    @CometUtilities.unstable_function_warning
    def lookup_commits(
            self,
            project: str,
            source_ref: str,
            parent_ref: str,
            filter_commits: bool = True,
            check_history: bool = False
    ) -> list:
        """Lookup/get new commits on source Git reference.

        Looks up and gets new commits on the source Git reference in comparison to the reference Git
        reference. It optionally supports filtering out ignored/useless commits.

        :param project: Target project path
        :param source_ref: Source Git reference
        :param parent_ref: Parent Git reference to compare the source Git reference with
        :param filter_commits: Filter out or remove ignored commits
        :param check_history:
            Override parent Git reference with last version commit hash if the version history is present
        :return: List of the commit hashes
        """
        history_commit_hash = None
        if check_history:
            if not self.project_config.has_deprecated_versioning_format():
                logger.debug(f"Looking up version commit hash in version history during commits lookup for "
                             f"[{project}] target project")
                history_commit_hash = \
                    self.project_config.get_project_history(project)["latest_bump_commit_hash"]
            else:
                logger.debug(f"Skipping version history check during commits lookup for [{project}] target "
                             f"project as it still using the deprecated versioning configuration format/schema")
        if history_commit_hash:
            logger.debug(f"Overriding provided parent reference [{parent_ref}] with the last version commit "
                         f"hash/reference [{history_commit_hash}] in the commits lookup for [{project}] target "
                         f"project")
            commits = self.scm.find_new_commits(
                source_ref,
                history_commit_hash,
                project
            )
        else:
            commits = self.scm.find_new_commits(
                source_ref,
                parent_ref,
                project
            )
        if filter_commits:
            commits = [
                commit for commit in commits if not ConventionalCommits.ignored_commit(
                    self.scm.get_commit_message(commit)
                )
            ]
        return commits

    @CometUtilities.unstable_function_warning
    def update_version_history(
            self,
            project: str,
            version_commit_hash: str,
            version_bump_type: str
    ) -> bool:
        """Update project version history in Comet configuration file.

        Updates project version history in Comet configuration file if the v1/new versioning configuration format
        or schema is used. In the new configuration format/schema, `history` and `version` parameters are provided
        instead of `dev_version` and `stable_version` parameters.

        :param project: Target project path
        :param version_commit_hash: Latest version commit hash to set in Comet version history (optional)
        :param version_bump_type: Latest version bump type to set in Comet version history (optional)
        :return: `True` if the version history is updated and `False` otherwise
        """
        if not self.project_config.has_deprecated_versioning_format():
            logger.debug(f"Updating version history in Comet configuration file for the target [{project}] project")
            self.project_config.update_project_history(
                project,
                version_bump_type,
                version_commit_hash
            )
            return True
        else:
            logger.debug(f"Skipping version history update in Comet configuration file for the "
                         f"[{project}] project due to v0/old configuration format/schema or missing "
                         f"version bump type and version commit hash")
            return False

    # TODO: Remove maybe
    @CometUtilities.unsupported_function_error
    def bump_dynamic_versions(self, project: str, commits: list, pre_release: str) -> int:
        """Bump the project version version dynamically.

        Execute dynamic version bumps for the project based on the type of commits provided. Dynamic here means
        that the version will be bumped according to the priority/type of previous version bump. This method also
        provides a :ivar:`pre_release` parameter to set the pre_release string for the version. ( Default: dev)

        :param project: Target project path
        :param commits: List of commit hashes to parse
        :param pre_release: Pre_release identifier to set (Required for dynamic versioning)
        :return: Latest version bump type
        """
        past_bump = SemVer.NO_CHANGE
        current_bump = SemVer.NO_CHANGE
        next_bump = SemVer.NO_CHANGE
        if not self.project_config.has_deprecated_versioning_format():
            past_bump = self.projects_semver_objects[project].get_version_enum_value(
                self.project_config.get_project_history(project)["next_release_type"]
            )

        for commit in commits:
            next_bump = ConventionalCommits.get_bump_type(
                self.scm.get_commit_message(commit)
            )
            logger.debug(
                f"Current Version: {self.projects_semver_objects[project].get_version()}, "
                f"Past Bump: {SemVer.SUPPORTED_RELEASE_TYPES[past_bump]}, "
                f"Current Bump: {SemVer.SUPPORTED_RELEASE_TYPES[current_bump]}, "
                f"Next Bump: {SemVer.SUPPORTED_RELEASE_TYPES[next_bump]}"
            )
            if next_bump == SemVer.NO_CHANGE:
                continue
            current_bump = self.projects_semver_objects[project].compare_bumps(past_bump, next_bump)
            self.projects_semver_objects[project].bump_version(
                release=current_bump, pre_release=pre_release)
            if current_bump == SemVer.PRE_RELEASE and past_bump > next_bump:
                continue
            else:
                past_bump = next_bump
        return past_bump


class GitFlow(WorkflowBase):
    """Backend to handle Gitflow based development work flows.

    This GitFlow backend implements customized Gitflow-based development work flows for Comet-managed projects. The
    GitFlow object provides work flows for branches and releases. Detailed overview of the work flows is given below:

    Branch Flows:
        Branch flows handle how to upgrade the versions and changelogs (Not developed yet) for the target Git
        branches according to the type of a branch.

        1. Stable branch
           Underdevelopment

        2. Development branch
           Development branch flow is executed for a branch specified in :ivar:`development_branch` parameter. It uses
           stable branch version as a reference. If new commits are found on the development branch in comparison to
           the stable branch, it will bump the development version according to the types of commits found. Versions
           bumps are performed for the keywords/identifiers found specified in the `ConventionalCommits` class.

           Versions on the development branch have an appended pre-release identifier `dev`.

           For example:

           Stable version =  1.0.0

           Current Dev version = 1.0.0-dev.1

           One minor change is merged to the development branch.

           New Dev version = 1.1.0-dev.1

           Another minor change is merged.

           New Dev version = 1.1.0-dev.2

           One major change is merged to the development branch.

           New Dev version = 2.0.0-dev.1

        3. Release branch
           Release branch flow is executed for branches with a prefix as specified in `release_branch_prefix` parameter
           in the Comet configuration file. It uses development version as a reference. If new commits are found on the
           release branch in comparison to the development branch, it will look for keywords/identifiers specified in
           the `ConventionalCommits` class for version upgrades and only bump the pre-release version.

           Versions on the release branch have an appended pre-release identifier `rc`.

           For example:

           Dev version =  1.0.0-dev.1

           Current release version = 1.0.0-rc.1

           One patch change is merged to the release branch.

           New release version = 1.0.0-rc.2

        4. Default branch (Feature/Bugfix/Misc)
           Default branch flow is executed for any branch that doesn't have a dedicated flow. If new commits are found
           in comparison to the development branch, it will upgrade the version by appending a 40 Bytes Hex version for
           latest SHA-1 commit hash as metadata. After the upgrade, it will commit the changes with an optional
           :ivar:`push_changes` flag that will push changes to the remote if it is set.

           For example:

           Dev version = 0.1.0-dev.1

           Default branch version =  0.1.0-dev.1+1d1f848c0a59b224206da26fbcae11e0bc5f5190

    Release Flows:
        1. Release Candidate branch
        2. Release to Stable branch


    handle how to upgrade the versions and changelogs (Not developed yet) for the target Git
    branches according to the type of a branch.

     . The idea is
    to have a class that handles all the Semantic Versioning related operations for the requested project. This class
    depends on `ConfigParser` class and is only supposed to be used with Comet too. It can be used with other tools if
    they follow the Comet philosophy or design.

    The SemVer object can read the reference version in the main project version file (.comet.yml usually), bump it
    according to the requested type of version bump and update the main project version file. Since, it depends on
    the Comet design, it can use two types of reference versions: `dev` and `stable`.
    This SemVer object also supports updating project specific version file paths using the provided regex pattern.

    .. important::
        Semver instance represents one project version only.

    Example:

    .. code-block:: python

        gitflow = GitFlow(
            connection_type="https",
            scm_provider="bitbucket",
            username="dummy",
            password="test",
            ssh_private_key_path="~/.ssh/id_rsa",
            project_local_path="./",
            project_config_path=".comet.yml",
            push_changes=False
        )

        gitflow.default_branch_flow()

    """

    def __init__(
            self,
            connection_type: str = "https",
            scm_provider: str = "bitbucket",
            username: str = "",
            password: str = "",
            ssh_private_key_path: str = "~/.ssh/id_rsa",
            project_local_path: str = "./",
            project_config_path: str = "./comet",
            push_changes: bool = False
    ) -> None:
        """
        Initializes a GitFlow object.

        :ivar connection_type: Git connection type for SCM provider
        :ivar scm_provider: Source Code Management Provider name
        :ivar username: Git username with write access to the project/repository
        :ivar password: Git user password with write access to the project/repository
        :ivar ssh_private_key_path: SSH private key file path on the local machine with write access to the project/repository
        :ivar project_config_path: Comet configuration file
        :ivar project_local_path: Local repository directory path
        :ivar push_changes: Optional flag to push changes to remote/upstream repository
        :return: None
        :raises Exception:
            raises an exception if it fails to execute work flow preparation steps
        """
        super().__init__(
            connection_type,
            scm_provider,
            username,
            password,
            ssh_private_key_path,
            project_local_path,
            project_config_path,
            push_changes
        )
        self.source_branch = None
        self.stable_branch = None
        self.development_branch = None
        self.release_branch_prefix = None
        self.prepare_branches()

    def prepare_branches(self) -> None:
        """
        Prepare the Git branches required as a pre-requisite for the GitFlow by generating the reference branch
        names according to the local Git repository state. In the method, the following operations are performed:

            1. Remote alias/upstream repository name is appended to the branch names if they don't exist locally
            on the remote/upstream Git repository
            2. Source branch name is set to the current active branch
            3. Stable and development branch names are set according to the Comet configuration

        :return: Returns `True` if the branches preparation is successful or `False`
                 otherwise
        :rtype: bool
        """
        try:
            self.source_branch = self.scm.get_active_branch()
            self.stable_branch = self.project_config.get_strategy_options()["stable_branch"]
            self.development_branch = self.project_config.get_strategy_options()["development_branch"]
            self.release_branch_prefix = self.project_config.get_strategy_options()["release_branch_prefix"]
            if (
                    not self.scm.has_local_branch(self.source_branch) or
                    not self.scm.has_local_branch(self.stable_branch) or
                    not self.scm.has_local_branch(self.development_branch)
            ):
                logger.debug(
                    f"Some of the Git branches does not exist locally. Using remote "
                    f"alias with branch names to access branches from the upstream "
                    f"repository"
                )
                assert self.scm.get_remote_alias(), \
                    f"No remote alias is not configured on the local " \
                    f"repository. Either configure a remote alias/upstream repository " \
                    f"or make sure all the required branches (stable, development and " \
                    f"source) exist on the local repository"

            if not self.scm.has_local_branch(self.source_branch):
                logger.debug(
                    f"Source branch [{self.source_branch}] does not exist locally"
                )
                logger.debug(
                    f"Adding remote alias [{self.scm.get_remote_alias()}] to the source branch name "
                    f"[{self.scm.get_remote_alias()}/{self.source_branch}]")
                self.source_branch = f"{self.scm.get_remote_alias()}/{self.source_branch}"
                assert self.scm.has_remote_branch(self.source_branch), \
                    f"Source branch [{self.source_branch}] does not exist on the remote alias/upstream repository" \
                    f"[{self.scm.get_remote_alias()}]"

            if not self.scm.has_local_branch(self.stable_branch):
                logger.debug(
                    f"Stable branch [{self.source_branch}] does not exist locally"
                )
                logger.debug(
                    f"Adding remote alias [{self.scm.get_remote_alias()}] to the stable branch name "
                    f"[{self.scm.get_remote_alias()}/{self.stable_branch}]")
                self.stable_branch = f"{self.scm.get_remote_alias()}/{self.stable_branch}"
                assert self.scm.has_remote_branch(self.stable_branch), \
                    f"Stable branch [{self.stable_branch}] does not exist on the remote alias/upstream repository" \
                    f"[{self.scm.get_remote_alias()}]"

            if not self.scm.has_local_branch(self.development_branch):
                logger.debug(
                    f"Development branch [{self.source_branch}] does not exist locally"
                )
                logger.debug(
                    f"Development branch [{self.development_branch}] not found locally. "
                    f"Adding remote alias [{self.scm.get_remote_alias()}] to the development branch name "
                    f"[{self.scm.get_remote_alias()}/{self.development_branch}]")
                self.development_branch = f"{self.scm.get_remote_alias()}/{self.development_branch}"
                assert self.scm.has_remote_branch(self.development_branch), \
                    f"Development branch [{self.development_branch}] does not exist on the remote alias/upstream " \
                    f"repository [{self.scm.get_remote_alias()}]"
        except AssertionError as err:
            logger.debug(err)
            raise Exception(
                f"Failed to prepare the required branches for the workflows. Verify that the required branches for "
                f"GitFlow based development exists in the local/remote Git repository"
            )

    @CometUtilities.unstable_function_warning
    def release_flow(self, branches: bool = False) -> None:
        """
        Executes the Release flow according to the specified parameters.
        There are two types of Release flows:
            1. Direct release of the source/active branch to the stable branch
            2. Release Candidate branch creation

        :param branches: Branches flag that specifies creation of release candidate branches only
        :return: None
        """
        if branches:
            assert len(self.project_config.config["projects"]) == 1, \
                f"Release flow is currently supported for repositories with one project only"
            self.release_candidate_flow()
        else:
            self.release_to_stable_flow(self.source_branch)

    def sync_flow(self) -> None:
        """
        Syncs the stable branch with the development branch.

        :return: None
        """
        logger.info(f"Syncing stable branch [{self.stable_branch}] with the development branch "
                    f"[{self.development_branch}]")
        self.scm.merge_branches(
            source_branch=self.stable_branch,
            destination_branch=self.development_branch
        )
        if self.push_changes:
            self.scm.push_changes(
                branch=self.development_branch,
                tags=False
            )

    def branch_flows(self) -> None:
        """
        Executes the branch flow according to the source or active branch on the local Git repository.

        :return: None
        """
        if self.source_branch == self.development_branch:
            self.development_branch_flow()
        elif self.source_branch == self.stable_branch:
            self.stable_branch_flow()
        elif self.release_branch_prefix in self.source_branch:
            self.release_branch_flow()
        else:
            self.default_branch_flow()

    @CometUtilities.unstable_function_warning
    def release_project_version(self, project: str, release_branch: str) -> bool:
        """Releases/finalizes the project version

        Releases/finalizes the project version, and upgrades the Comet configuration file and project specific
        version files. The version is finalized for a project only if the new changes/commits are found on
        :ivar:`release_branch` in reference to the stable branch.

        :param project: Target project path.
        :param release_branch: Git branch to release to the stable branch.
        :return: `True` if the project is released and `False` otherwise.
        """
        current_dev_version = self.projects_semver_objects[project].get_version()
        release_version = self.projects_semver_objects[project].get_final_version()
        commits = self.scm.find_new_commits(
            release_branch,
            self.stable_branch,
            project
        )
        if commits:
            logger.info(f"Release version '{release_version}' for the project [{project}]")
            self.projects_semver_objects[project].update_version_files(
                current_dev_version,
                release_version
            )
            self.project_config.update_project_version(
                project,
                release_version,
                version_type=self._set_deprecated_version_type("stable")
            )
            if self.project_config.has_deprecated_versioning_format():
                self.project_config.update_project_version(
                    project,
                    release_version,
                    version_type=self._set_deprecated_version_type("dev")
                )
            self.update_version_history(
                project,
                None,
                SemVer.SUPPORTED_RELEASE_TYPES[SemVer.NO_CHANGE]
            )
            return True
        else:
            logger.debug(f"Skipping release for sub-project [{project}]")
            return False

    @CometUtilities.unstable_function_warning
    def release_to_stable_flow(self, release_branch: str) -> list:
        """Releases a new version for the Comet-managed project(s).

        Checks out to the stable branch, merges the development branch into the stable branch, updates all the relevant
        version files to this new stable version and checks out back to the development branch.

        :param release_branch: Git branch to release to the stable branch.
        :return: List of changed/released projects
        """
        allowed_branches = [
            self.development_branch,
            self.release_branch_prefix
        ]
        assert len([match for match in allowed_branches if (match in release_branch)]) > 0, \
            f"Only development branch and release candidate branches are allowed to be released!"
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("dev"))
        changed_projects = []
        for project in self.project_config.config["projects"]:
            if self.release_project_version(project["path"], release_branch):
                changed_projects.append(project["path"])

        if len(changed_projects) > 0:
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
            self.scm.merge_branches(
                source_branch=self.source_branch,
                destination_branch=self.stable_branch
            )

        for project in changed_projects:
            release_version = self.projects_semver_objects[project].get_final_version()
            project_name = os.path.basename(project).strip('.')
            self.scm.add_tag(f"{project_name}{'-' if project_name else ''}{release_version}")

        if self.push_changes:
            self.scm.push_changes(
                branch=self.stable_branch,
                tags=True
            )
        return changed_projects

    @CometUtilities.unstable_function_warning
    def create_project_rc(self, project: str) -> bool:
        """Create a release candidate for the project.

        Creates a Release Candidate branch for the project version, and upgrades the Comet configuration file and
        project specific version files accordingly. The Release Candidate branch only if it does not exist.

        :param project: Target project path.
        :return: `True` if the project is released and `False` otherwise.
        """
        release_candidate = self.projects_semver_objects[project].get_final_version()
        logger.info(f"Creating a Release candidate [{release_candidate}]")
        release_candidate_branch = f"{self.release_branch_prefix}/{release_candidate}"
        if self.scm.has_local_branch(release_candidate_branch) or self.scm.has_remote_branch(release_candidate_branch):
            logger.debug(f"Skipping Release Candidate as the branch [{release_candidate_branch}] already exists on "
                         f"the local or remote repository")
            return False
        self.scm.add_branch(
            release_candidate_branch,
            checkout=True
        )
        self.projects_semver_objects[project].bump_version(
            release=SemVer.PRE_RELEASE, pre_release="rc")
        current_version = self.project_config.get_project_version(
            project,
            version_type=self._set_deprecated_version_type("dev")
        )
        new_version = self.projects_semver_objects[project].get_version()
        self.projects_semver_objects[project].update_version_files(
            current_version,
            new_version
        )
        self.project_config.update_project_version(
            project,
            new_version,
            version_type=self._set_deprecated_version_type("dev")
        )
        return True

    @CometUtilities.unstable_function_warning
    def release_candidate_flow(self) -> list:
        """
        Creates the release candidate(s) for the Comet-managed project(s).
        Creates a release candidate branch according to the development version for a project and checks out to this
        branch. After the checkout, it updates versions to include `rc` identifier specifying a release candidate.

        :return: List of projects for which the release candidate branches are created
        """
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("dev"))

        changed_projects = []
        for project in self.project_config.config["projects"]:
            if self.create_project_rc(project["path"]):
                changed_projects.append(project['path'])

        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for {', '.join(changed_projects)} projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        return changed_projects

    # TODO: Add Assertion check for source branch
    # TODO: Return False if commits are found but no version is upgraded.
    @CometUtilities.unstable_function_warning
    def upgrade_stable_branch_project_version(self, project: str) -> bool:
        """Upgrade the project version in stable branch.

        Upgrades the project version for the stable Git branch in the Comet configuration file and project
        specific version files.

        :param project: Target project path.
        """
        commits = self.lookup_commits(
            project,
            self.source_branch,
            self.development_branch,
            filter_commits=True,
            check_history=True
        )

        if not commits:
            logger.info(f"No new commits are found on the stable branch for the target [{project}] project")
            return False

        last_bump_type = self.bump_project_version(
            project,
            commits,
            pre_release_str=None,
            pre_release_only=False,
            check_history=False
        )

        current_version = self.project_config.get_project_version(
            project,
            version_type=self._set_deprecated_version_type("stable")
        )
        new_version = self.projects_semver_objects[project].get_version()

        if current_version != new_version:
            logger.debug(f"Updating version files for the target [{project}] project")
            self.projects_semver_objects[project].update_version_files(
                current_version,
                new_version
            )
            logger.debug(f"Updating version/s in Comet configuration file for the target [{project}] project")
            self.project_config.update_project_version(
                project,
                new_version,
                version_type=self._set_deprecated_version_type("stable")
            )
            if not self.update_version_history(
                    project,
                    self.scm.get_commit_hexsha(commits[-1], short=True),
                    SemVer.SUPPORTED_RELEASE_TYPES[last_bump_type]
            ):
                self.project_config.update_project_version(
                    project,
                    new_version,
                    version_type=self._set_deprecated_version_type("dev")
                )
        return True

    @CometUtilities.unstable_function_warning
    def stable_branch_flow(self):
        """Execute Stable branch versioning flow for the Comet managed projects.

        Executes the stable branch versioning flow according to the designed/implemented Git flow. Stable branch flow
        is only executed for the branch specified in `stable_branch` parameter in the Comet configuration file. It
        uses development version as a reference. If new commits are found on the stable branch
        in comparison to the development branch, it will look for keywords/identifiers specified in the
        `ConventionalCommits` class for version upgrades and only bump the stable version.

        This branch flow must is recommended to be executed for patches/fixes on the stable branch.

        :return: List of changed projects
        """
        logger.info("Executing Stable branch GitFlow")
        logger.warning(
            f"Stable branch GitFlow bumps version on every execution if new commits are found in comparison to "
            f"the Development branch regardless of if they are already catered for in the version bump. Please "
            f"make sure to merge all the version bumps on a Stable branch into the Development branch after the "
            f"execution."
        )
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("stable"))
        changed_projects = []
        # TODO: Initialize versioning variables
        for project in self.project_config.config["projects"]:
            if self.upgrade_stable_branch_project_version(project["path"]):
                changed_projects.append(project['path'])
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for {', '.join(changed_projects)} projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        for project in changed_projects:
            release_version = self.projects_semver_objects[project].get_final_version()
            project_name = os.path.basename(project).strip('.')
            self.scm.add_tag(f"{project_name}{'-' if project_name else ''}{release_version}")
        if self.push_changes:
            self.scm.push_changes(
                branch=self.stable_branch,
                tags=True
            )
        return changed_projects

    @CometUtilities.unstable_function_warning
    def upgrade_default_branch_project_version(self, project: str) -> bool:
        """Upgrade the project version in development branch.

        Upgrades the project version for the default/any Git branch in the Comet configuration file and project
        specific version files.

        :param project: Target project path.
        """
        commits = self.lookup_commits(
            project,
            self.source_branch,
            self.development_branch,
            filter_commits=True,
            check_history=True
        )
        if not commits:
            logger.info(f"No new commits are found on the default branch for the target [{project}] project")
            return False
        current_version = self.projects_semver_objects[project].get_version()
        last_bump_type = self.bump_project_version(
            project,
            commits,
            pre_release_str="dev",
            pre_release_only=False,
            build_only=True,
            check_history=True
        )
        new_version = self.projects_semver_objects[project].get_version()

        if current_version != new_version:
            logger.debug(f"New commits found for the target project [{project}] "
                         f"in reference to development branch [{self.development_branch}]")
            logger.debug(f"Updating version files with a new version [{new_version}] for the "
                         f"target [{project}] project")
            self.projects_semver_objects[project].update_version_files(
                current_version,
                new_version
            )
            logger.debug(f"Updating version/s in Comet configuration file for the target [{project}] project")
            self.project_config.update_project_version(
                project,
                new_version,
                version_type=self._set_deprecated_version_type("dev")
            )
            self.update_version_history(
                project,
                self.scm.get_commit_hexsha(commits[-1], short=True),
                SemVer.SUPPORTED_RELEASE_TYPES[last_bump_type]
            )
            return True
        else:
            logger.debug(f"Skipping version upgrade for the target [{project}] project")
            return False

    def default_branch_flow(self) -> list:
        """
        Executes the default branch flow according to the designed/implemented Git flow. Default branch flow is
        executed for any branch that doesn't have a dedicated branch flow. If new commits are found in comparison
        to the development branch, it will upgrade the version by appending a 40 Bytes Hex version for latest SHA-1
        commit hash as metadata. After the upgrade, it will commit the changes with an optional :ivar:`push_changes`
        flag that will push changes to the remote if it is set.

        :return: List of changed/upgraded projects
        """
        logger.info("Executing default branch GitFlow")
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("dev"))
        changed_projects = []
        for project in self.project_config.config["projects"]:
            if self.upgrade_default_branch_project_version(project["path"]):
                changed_projects.append(project['path'])
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for the target [{', '.join(changed_projects)}] projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        return changed_projects

    # TODO: Add Assertion check for source branch
    @CometUtilities.unstable_function_warning
    def upgrade_dev_branch_project_version(self, project: str) -> bool:
        """Upgrade the project version in development branch.

        Upgrades the project version for the development Git branch in the Comet configuration file and project
        specific version files.

        :param project: Target project path.
        """
        commits = self.lookup_commits(
            project,
            self.development_branch,
            self.stable_branch,
            filter_commits=True,
            check_history=True
        )
        if not commits:
            logger.info(f"No new commits are found on the development branch for the target [{project}] project")
            return False
        current_version = self.project_config.get_project_version(
            project,
            version_type=self._set_deprecated_version_type("dev")
        )
        last_bump_type = self.bump_project_version(
            project,
            commits,
            pre_release_str="dev",
            pre_release_only=False,
            check_history=True
        )
        new_version = self.projects_semver_objects[project].get_version()

        if current_version != new_version:
            logger.debug(f"Updating version files for the target [{project}] project")
            self.projects_semver_objects[project].update_version_files(
                current_version,
                new_version
            )
            logger.debug(f"Updating version/s in Comet configuration file for the target [{project}] project")
            self.project_config.update_project_version(
                project,
                new_version,
                version_type=self._set_deprecated_version_type("dev")
            )
            self.update_version_history(
                project,
                self.scm.get_commit_hexsha(commits[-1], short=True),
                SemVer.SUPPORTED_RELEASE_TYPES[last_bump_type]
            )
            return True
        else:
            logger.debug(f"Skipping version upgrade for the target [{project}] project")
            return False

    # TODO: Verify loop for projects as it still says Upgrades found even when there are no files.
    def development_branch_flow(self):
        """
        Executes the development branch flow according to the designed/implemented Git flow. Development branch
        flow is executed for a branch specified in :ivar:`development_branch` parameter. It uses stable branch
        version as a reference. If new commits are found on the development branch in comparison to the stable
        branch, it will bump the development version according to the types of commits found. Versions bumps are
        performed for the keywords/identifiers found specified in the `ConventionalCommits` class.

        :return: None
        """
        logger.info("Executing Development branch GitFlow")
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("stable"))
        changed_projects = []
        for project in self.project_config.config["projects"]:
            if self.upgrade_dev_branch_project_version(project["path"]):
                changed_projects.append(project['path'])
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for [{', '.join(changed_projects)}] projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        return changed_projects

    # TODO: Add Assertion check for source branch
    @CometUtilities.unstable_function_warning
    def upgrade_release_branch_project_version(self, project: str) -> bool:
        """Upgrade the project version in release branches.

        Upgrades the project version for the release Git branch/es in the Comet configuration file and project
        specific version files.

        :param project: Target project path.
        """
        commits = self.lookup_commits(
            project,
            self.source_branch,
            self.development_branch,
            filter_commits=True,
            check_history=True
        )
        if not commits:
            logger.info(f"No new commits are found on the development branch for the target [{project}] project")
            return False
        current_version = self.project_config.get_project_version(
            project,
            version_type=self._set_deprecated_version_type("dev")
        )
        last_bump_type = self.bump_project_version(
            project,
            commits,
            pre_release_str="rc",
            pre_release_only=True,
            check_history=False
        )
        new_version = self.projects_semver_objects[project].get_version()

        if current_version != new_version:
            logger.debug(f"Updating version files for the target [{project}] project")
            self.projects_semver_objects[project].update_version_files(
                current_version,
                new_version
            )
            logger.debug(f"Updating version/s in Comet configuration file for the target [{project}] project")
            self.project_config.update_project_version(
                project,
                new_version,
                version_type=self._set_deprecated_version_type("dev")
            )
            self.update_version_history(
                project,
                self.scm.get_commit_hexsha(commits[-1], short=True),
                SemVer.SUPPORTED_RELEASE_TYPES[last_bump_type]
            )
            return True
        else:
            logger.debug(f"Skipping version upgrade for the target [{project}] project")
            return False

    # TODO: Initialize RC branch with rc.1 whenever it is created
    @CometUtilities.unstable_function_warning
    def release_branch_flow(self):
        """
        Executes the release branch flow according to the designed/implemented Git flow. Release branch flow is
        executed for branches with a prefix as specified in `release_branch_prefix` parameter in the Comet
        configuration file. It uses development version as a reference. If new commits are found on the release branch
        in comparison to the development branch, it will look for keywords/identifiers specified in the
        `ConventionalCommits` class for version upgrades and only bump the pre-release version.

        :return: None
        """
        logger.info("Executing Release branch GitFlow")
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("dev"))
        changed_projects = []
        for project in self.project_config.config["projects"]:
            if self.upgrade_release_branch_project_version(project["path"]):
                changed_projects.append(project['path'])
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for [{', '.join(changed_projects)}] sub-projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        return changed_projects
