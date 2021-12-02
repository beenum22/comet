# from typing import TypedDict, List, Dict
import logging
import os
from .scm import Scm
from .semver import SemVer
from .conventions import ConventionalCommits
from .config import ConfigParser
from .utilities import CometUtilities

logger = logging.getLogger(__name__)


class GitFlow(object):
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
        self.source_branch = None
        self.stable_branch = None
        self.development_branch = None
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
    def _has_deprecated_versioning_format(self) -> bool:
        """
        Returns true if the deprecated versioning format is configured where 'dev_version' and 'stable_version'
        parameters are configured for any Comet-managed project.

        :return:
            Returns the 'True' if the deprecated versioning format is configured or 'False' otherwise
        """
        if self.project_config.has_deprecated_config_parameter("dev_version") or \
                self.project_config.has_deprecated_config_parameter("stable_version"):
            logger.warning(
                f"Deprecated versioning format is configured for the Comet-managed projects that uses 'dev_version' "
                f"and 'stable_version' parameters"
            )
            return True
        return False

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
        if self._has_deprecated_versioning_format():
            logger.warning(
                f"Version type is configured for the deprecated project versioning logic that uses 'dev_version' "
                f"and 'stable_version' parameters"
            )
            return version_type
        return None

    def _prepare_branches(self) -> None:
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
            self.stable_branch = self.project_config.config["stable_branch"]
            self.development_branch = self.project_config.config["development_branch"]
            self.release_branch_prefix = self.project_config.config["release_branch_prefix"]
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
            self.project_config.read_config(sanitize=True)

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

            self._prepare_branches()
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
            self.release_candidate()
        else:
            self.release_to_stable(self.source_branch)

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
        if self.source_branch == self.project_config.config["development_branch"]:
            self.development_branch_flow()
        elif self.source_branch == self.project_config.config["stable_branch"]:
            self.stable_branch_flow()
        elif self.project_config.config["release_branch_prefix"] in self.source_branch:
            self.release_branch_flow()
        else:
            self.default_branch_flow()

    @CometUtilities.unstable_function_warning
    def release_to_stable(self, release_branch: str) -> None:
        """Releases a new version for the Comet-managed project(s).

        Checks out to the stable branch, merges the development branch into the stable branch, updates all the relevant
        version files to this new stable version and checks out back to the development branch.

        :param release_branch: Git branch to release to the stable branch.
        :return: None
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
            current_dev_version = self.projects_semver_objects[project['path']].get_version()
            release_version = self.projects_semver_objects[project['path']].get_final_version()
            commits = self.scm.find_new_commits(
                release_branch,
                self.stable_branch,
                project["path"]
            )
            if commits:
                logger.info(f"Release version '{release_version}' for the project [{project['path']}]")
                self.projects_semver_objects[project["path"]].update_version_files(
                    current_dev_version,
                    release_version
                )
                self.project_config.update_project_version(
                    project["path"],
                    release_version,
                    version_type=self._set_deprecated_version_type("stable")
                )
                if self._has_deprecated_versioning_format():
                    self.project_config.update_project_version(
                        project["path"],
                        release_version,
                        version_type=self._set_deprecated_version_type("dev")
                    )
                changed_projects.append(project['path'])
            else:
                logger.debug(f"Skipping release for sub-project [{project['path']}]")

        if len(changed_projects) > 0:
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
            self.scm.merge_branches(
                source_branch=self.development_branch,
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

    @CometUtilities.unstable_function_warning
    def release_candidate(self) -> None:
        """
        Creates the release candidate(s) for the Comet-managed project(s).
        Creates a release candidate branch according to the development version for a project and checks out to this
        branch. After the checkout, it updates versions to include `rc` identifier specifying a release candidate.

        :return: None
        """
        version_type = None
        if "version" not in self.project_config.config["projects"][0]:
            logger.warning(f"Deprecated version parameters [dev_version, stable_version] are set in the "
                           f"Comet configuration")
            version_type = "dev"
        self.prepare_versioning(reference_version_type=version_type)

        changed_projects = []
        for project in self.project_config.config["projects"]:
            release_candidate = self.projects_semver_objects[project['path']].get_final_version()
            logger.info(f"Creating a Release candidate [{release_candidate}]")
            self.scm.add_branch(
                f"{self.project_config.config['release_branch_prefix']}/{release_candidate}",
                checkout=True
            )
            self.projects_semver_objects[project["path"]].bump_version(
                release=SemVer.PRE_RELEASE, pre_release="rc")
            current_version = self.project_config.get_project_version(
                project["path"],
                version_type="dev"
            )
            new_version = self.projects_semver_objects[project['path']].get_version()
            self.projects_semver_objects[project["path"]].update_version_files(
                current_version,
                new_version
            )
            self.project_config.update_project_version(
                project["path"],
                new_version,
                version_type="dev"
            )

            changed_projects.append(project['path'])

        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for {', '.join(changed_projects)} projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )

    @CometUtilities.unstable_function_warning
    def stable_branch_flow(self):
        """
        Executes the stable branch flow according to the designed Git flow process.

        .. important::
            Underdevelopment!

        :return: None
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

            if "history" in project and project["history"]["latest_bump_commit_hash"]:
                commits = self.scm.find_new_commits(
                    self.source_branch,
                    self.project_config.get_project_history(project["path"])["latest_bump_commit_hash"],
                    project["path"]
                )
            else:
                commits = self.scm.find_new_commits(
                    self.stable_branch,
                    self.development_branch,
                    project["path"]
                )
            commits = [
                commit for commit in commits if not ConventionalCommits.ignored_commit(
                    self.scm.get_commit_message(commit)
                )
            ]

            for commit in commits:
                next_bump = ConventionalCommits.get_bump_type(
                    self.scm.get_commit_message(commit)
                )
                logger.debug(
                    f"Current Version: {self.projects_semver_objects[project['path']].get_version()}, "
                    f"Next Bump: {SemVer.SUPPORTED_RELEASE_TYPES[next_bump]}"
                )
                if next_bump == SemVer.NO_CHANGE:
                    continue
                self.projects_semver_objects[project["path"]].bump_version(
                    release=next_bump, pre_release=None)
            current_version = self.project_config.get_project_version(
                project["path"],
                version_type=self._set_deprecated_version_type("stable")
            )
            new_version = self.projects_semver_objects[project['path']].get_version()
            if current_version != new_version:
                self.projects_semver_objects[project["path"]].update_version_files(
                    current_version,
                    new_version
                )
                self.project_config.update_project_version(
                    project["path"],
                    new_version,
                    version_type=self._set_deprecated_version_type("stable")
                )
                if not self._has_deprecated_versioning_format():
                    new_version_hex = self.scm.get_commit_hexsha(commits[-1], short=True)
                    self.project_config.update_project_history(
                        project["path"],
                        SemVer.SUPPORTED_RELEASE_TYPES[next_bump],
                        new_version_hex
                    )
                else:
                    self.project_config.update_project_version(
                        project["path"],
                        new_version,
                        version_type=self._set_deprecated_version_type("dev")
                    )
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

    def default_branch_flow(self) -> None:
        """
        Executes the default branch flow according to the designed/implemented Git flow. Default branch flow is
        executed for any branch that doesn't have a dedicated branch flow. If new commits are found in comparison
        to the development branch, it will upgrade the version by appending a 40 Bytes Hex version for latest SHA-1
        commit hash as metadata. After the upgrade, it will commit the changes with an optional :ivar:`push_changes`
        flag that will push changes to the remote if it is set.

        :return: None
        """
        logger.info("Executing default branch GitFlow")
        self.prepare_versioning(reference_version_type=self._set_deprecated_version_type("dev"))
        changed_projects = []
        for project in self.project_config.config["projects"]:
            current_version = self.projects_semver_objects[project['path']].get_version()
            logger.debug(
                f"Current Version for sub-project [{project['path']}]: {current_version}"
            )
            if "history" in project and project["history"]["latest_bump_commit_hash"]:
                commits = self.scm.find_new_commits(
                    self.source_branch,
                    self.project_config.get_project_history(project["path"])["latest_bump_commit_hash"],
                    project["path"]
                )
            else:
                commits = self.scm.find_new_commits(
                    self.source_branch,
                    self.development_branch,
                    project["path"]
                )
            commits = [
                commit for commit in commits if not ConventionalCommits.ignored_commit(
                    self.scm.get_commit_message(commit)
                )
            ]
            if commits:
                version_hex_change = False
                current_version_hex = None
                new_version_hex = self.scm.get_commit_hexsha(commits[-1], short=True)
                if self.projects_semver_objects[project['path']].version_object.build:
                    current_version_hex = \
                        self.projects_semver_objects[project['path']].version_object.build.split(".")[0]
                if not current_version_hex or (current_version_hex and current_version_hex != new_version_hex):
                    version_hex_change = True

                if version_hex_change:
                    logger.debug(f"New commits found for project [{project['path']}] "
                                 f"in reference to development branch [{self.development_branch}]")
                    self.projects_semver_objects[project["path"]].bump_version(
                        release=SemVer.BUILD,
                        pre_release="dev",
                        build_metadata=f"{new_version_hex}",
                        static_build_metadata=True
                    )
            if self.projects_semver_objects[project['path']].get_version() != current_version:
                new_version = self.projects_semver_objects[project['path']].get_version()
                logger.debug(f"New Version for sub-project [{project['path']}]: {new_version}")
                self.projects_semver_objects[project["path"]].update_version_files(
                    current_version,
                    new_version
                )
                self.project_config.update_project_version(
                    project["path"],
                    new_version,
                    version_type=self._set_deprecated_version_type("dev")
                )
                changed_projects.append(project['path'])
            else:
                logger.debug(f"Skipping version upgrade for sub-project [{project['path']}]")
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for [{', '.join(changed_projects)}] sub-projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        else:
            logger.info(f"No version upgrade/s found for sub-projects")

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
        version_type = None
        if "version" not in self.project_config.config["projects"][0]:
            version_type = "dev"
        self.prepare_versioning(reference_version_type=version_type)
        changed_projects = []
        for project in self.project_config.config["projects"]:
            if "release_commit_sha" in project and project["release_commit_sha"]:
                commits = self.scm.find_new_commits(
                    self.source_branch,
                    project["release_commit_sha"],
                    project["path"]
                )
            else:
                commits = self.scm.find_new_commits(
                    self.source_branch,
                    self.development_branch,
                    project["path"]
                )
            commits = [
                commit for commit in commits if not ConventionalCommits.ignored_commit(
                    self.scm.get_commit_message(commit)
                )
            ]

            for commit in commits:
                next_bump = ConventionalCommits.get_bump_type(
                    self.scm.get_commit_message(commit)
                )
                logger.debug(
                    f"Current Version: {self.projects_semver_objects[project['path']].get_version()}"
                )
                if next_bump == SemVer.NO_CHANGE:
                    continue
                self.projects_semver_objects[project["path"]].bump_version(
                    release=SemVer.PRE_RELEASE, pre_release="rc")
            current_version = self.project_config.get_project_version(
                project["path"],
                version_type="dev"
            )
            new_version = self.projects_semver_objects[project['path']].get_version()
            if current_version != new_version:
                self.projects_semver_objects[project["path"]].update_version_files(
                    current_version,
                    new_version
                )
                self.project_config.update_project_version(
                    project["path"],
                    new_version,
                    version_type=version_type
                )
                changed_projects.append(project['path'])
            else:
                logger.debug(f"Skipping version upgrade for sub-project [{project['path']}]")
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for [{', '.join(changed_projects)}] sub-projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        else:
            logger.info(f"No version upgrade/s found for sub-projects")

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
            if not self._has_deprecated_versioning_format():
                past_bump = self.projects_semver_objects[project["path"]].get_version_enum_value(
                    self.project_config.get_project_history(project["path"])["latest_bump_type"]
                )
            else:
                past_bump = SemVer.NO_CHANGE
            current_bump = SemVer.NO_CHANGE
            current_version = self.project_config.get_project_version(
                project["path"],
                version_type=self._set_deprecated_version_type("dev")
            )
            if "history" in project and project["history"]["latest_bump_commit_hash"]:
                commits = self.scm.find_new_commits(
                    self.source_branch,
                    self.project_config.get_project_history(project["path"])["latest_bump_commit_hash"],
                    project["path"]
                )
            else:
                commits = self.scm.find_new_commits(
                    self.development_branch,
                    self.stable_branch,
                    project["path"]
                )
            commits = [
                commit for commit in commits if not ConventionalCommits.ignored_commit(
                    self.scm.get_commit_message(commit)
                )
            ]

            for commit in commits:
                next_bump = ConventionalCommits.get_bump_type(
                    self.scm.get_commit_message(commit)
                )
                logger.debug(
                    f"Current Version: {self.projects_semver_objects[project['path']].get_version()}, "
                    f"Past Bump: {SemVer.SUPPORTED_RELEASE_TYPES[past_bump]}, "
                    f"Current Bump: {SemVer.SUPPORTED_RELEASE_TYPES[current_bump]}, "
                    f"Next Bump: {SemVer.SUPPORTED_RELEASE_TYPES[next_bump]}"
                )
                if next_bump == SemVer.NO_CHANGE:
                    continue
                current_bump = self.projects_semver_objects[project["path"]].compare_bumps(past_bump, next_bump)
                self.projects_semver_objects[project["path"]].bump_version(
                    release=current_bump, pre_release="dev")
                if current_bump == SemVer.PRE_RELEASE and past_bump > next_bump:
                    continue
                else:
                    past_bump = next_bump
            new_version = self.projects_semver_objects[project['path']].get_version()
            if current_version != new_version:
                self.projects_semver_objects[project["path"]].update_version_files(
                    current_version,
                    new_version
                )
                self.project_config.update_project_version(
                    project["path"],
                    new_version,
                    version_type=self._set_deprecated_version_type("dev")
                )
                if not self._has_deprecated_versioning_format():
                    new_version_hex = self.scm.get_commit_hexsha(commits[-1], short=True)
                    self.project_config.update_project_history(
                        project["path"],
                        SemVer.SUPPORTED_RELEASE_TYPES[past_bump],
                        new_version_hex
                    )
                changed_projects.append(project['path'])
            else:
                logger.debug(f"Skipping version upgrade for sub-project [{project['path']}]")
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for [{', '.join(changed_projects)}] sub-projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )
        else:
            logger.info(f"No version upgrade/s found for sub-projects")
