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
        self.connection_type = connection_type
        self.scm_provider = scm_provider
        self.username = username
        self.password = password
        self.ssh_private_key_path = ssh_private_key_path
        self.project_config_path = project_config_path
        self.project_local_path = project_local_path
        self.push_changes = push_changes
        self.scm = None
        self.project_config = {}
        self.projects_semver_objects = {}
        self.prepare_workflow()

    def _sanitize_paths(self) -> None:
        logger.debug(f"Sanitizing paths according to the root/repo directory [{self.project_local_path}]")
        self.project_local_path = os.path.normpath(f"{self.project_local_path}")
        self.project_config_path = os.path.normpath(f"{self.project_local_path}/{self.project_config_path}")
        # self.projects = [os.path.normpath(f"{self.project_local_path}/{project}") for project in self.projects]
        logger.debug(f"Sanitized paths according to the root/repo directory [{self.project_local_path}]")

    def _generate_projects_mapping(self) -> None:
        logger.debug(f"Generating sub-projects information mapping")
        common_prefix = os.path.commonprefix(self.projects)
        for project in self.projects:
            project['semver_object'] = SemVer(
                project_path=project,
                version_files=project[version_files]
            )
            project_mapping = {
                "name": project.replace(common_prefix, ""),
                "path": project,
                "semver_object": None
            }
            self.projects_info.append(project_mapping)
        logger.debug(f"Generated sub-projects information mapping: {self.projects_info}")

    def prepare_workflow(self) -> None:
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
                ssh_private_key_path=self.ssh_private_key_path,
                development_branch=self.project_config.config["development_branch"],
                stable_branch=self.project_config.config["stable_branch"]
            )
        except Exception:
            raise

    def prepare_versioning(self, reference_version_type: str = "stable") -> None:
        try:
            assert reference_version_type in ConfigParser.SUPPORTED_VERSION_TYPES, \
                f"Invalid reference version type" \
                f"[{reference_version_type}({ConfigParser.SUPPORTED_VERSION_TYPES})] specified! " \
                f"Supported values are [{','.join([str(i) for i in ConfigParser.SUPPORTED_VERSION_TYPES])}]"
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
    def release_flow(self, branches: bool = False):
        if branches:
            assert len(self.project_config.config["projects"]) > 0, \
                f"Release flow is currently supported for repositories with one project only"
        self.prepare_versioning("dev")
        changed_projects = []
        for project in self.project_config.config["projects"]:
            release_candidate = self.projects_semver_objects[project['path']].get_final_version()
            logger.info(f"Creating a Release candidate [{release_candidate}]")
            if branches:
                self.scm.add_branch(
                    f"{self.project_config.config['release_branch_prefix']}/{release_candidate}",
                    checkout=True
                )
                self.projects_semver_objects[project["path"]].bump_version(
                    release=SemVer.PRE_RELEASE, pre_release="rc")
                self.projects_semver_objects[project["path"]].update_version_files(
                    self.projects_semver_objects[project["path"]]._read_default_version_file(version_type="dev")
                )
                changed_projects.append(project['path'])
            else:
                logger.error(f"Release is not implemented yet!")
        if len(changed_projects) > 0:
            logger.info(f"Version upgrade/s found for {', '.join(changed_projects)} projects")
            self.scm.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.project_config_path,
                *changed_projects,
                push=self.push_changes
            )

    def branch_flows(self):
        if self.scm.source_branch == self.project_config.config["development_branch"]:
            self.development_branch_flow()
        elif self.scm.source_branch == self.project_config.config["stable_branch"]:
            self.stable_branch_flow()
        elif self.project_config.config["release_branch_prefix"] in self.scm.source_branch:
            self.release_branch_flow()
        else:
            self.default_branch_flow()

    def stable_branch_flow(self):
        logger.info("Executing Stable branch GitFlow")
        self.prepare_versioning("stable")
        changed_projects = []
        for project in self.project_config.config["projects"]:
            past_bump = SemVer.NO_CHANGE
            current_bump = SemVer.NO_CHANGE
            commits = self.scm.find_new_commits(
                self.scm.development_branch,
                self.scm.stable_branch,
                project["path"]
            )
            for commit in commits:
                next_bump = ConventionalCommits.get_bump_type(commit.message)
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
                    release=current_bump, pre_release=None)
                if current_bump == SemVer.PRE_RELEASE and past_bump > next_bump:
                    continue
                else:
                    past_bump = next_bump
            self.projects_semver_objects[project["path"]].update_version_files(
                self.projects_semver_objects[project["path"]]._read_default_version_file(version_type="dev")
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

    def default_branch_flow(self) -> None:
        logger.info("Executing default branch GitFlow")
        self.prepare_versioning("dev")
        changed_projects = []
        for project in self.project_config.config["projects"]:
            current_version = self.projects_semver_objects[project['path']].get_version()
            logger.debug(
                f"Current Version for sub-project [{project['path']}]: {current_version}"
            )
            commits = self.scm.find_new_commits(
                self.scm.source_branch,
                self.scm.development_branch,
                project["path"]
            )
            commits = [
                commit for commit in commits if not ConventionalCommits.ignored_commit(commit.message)
            ]
            if commits:
                current_version_hex = None
                commit_hexes = [commit.hexsha for commit in commits]
                if self.projects_semver_objects[project['path']].version_object.build:
                    current_version_hex = \
                        self.projects_semver_objects[project['path']].version_object.build.split(".")[0]
                if current_version_hex and len(commit_hexes) > 1 and current_version_hex in commit_hexes:
                    new_version_hex = commit_hexes[-1]
                else:
                    new_version_hex = commit_hexes[0]
                if new_version_hex:
                    logger.debug(f"New commits found for project [{project['path']}] "
                                 f"in reference to development branch [{self.scm.development_branch}]")
                    self.projects_semver_objects[project["path"]].bump_version(
                        release=SemVer.BUILD,
                        pre_release="dev",
                        build_metadata=f"{new_version_hex}",
                        static_build_metadata=True
                    )
            if self.projects_semver_objects[project['path']].get_version() != current_version:
                logger.debug(f"New Version for sub-project [{project['path']}]: "
                             f"{self.projects_semver_objects[project['path']].get_version()}")
                self.projects_semver_objects[project["path"]].update_version_files(
                    current_version
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

    @CometUtilities.unstable_function_warning
    def release_branch_flow(self):
        logger.info("Executing Release branch GitFlow")
        self.prepare_versioning("dev")
        changed_projects = []
        for project in self.project_config.config["projects"]:
            commits = self.scm.find_new_commits(
                self.scm.source_branch,
                self.scm.development_branch,
                project["path"]
            )
            for commit in commits:
                next_bump = ConventionalCommits.get_bump_type(commit.message)
                logger.debug(
                    f"Current Version: {self.projects_semver_objects[project['path']].get_version()}"
                )
                if next_bump == SemVer.NO_CHANGE:
                    continue
                self.projects_semver_objects[project["path"]].bump_version(
                    release=SemVer.PRE_RELEASE, pre_release="rc")
            self.projects_semver_objects[project["path"]].update_version_files(
                self.projects_semver_objects[project["path"]]._read_default_version_file(version_type="dev")
            )
            changed_projects.append(project['path'])
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
        logger.info("Executing Development branch GitFlow")
        self.prepare_versioning("stable")
        changed_projects = []
        for project in self.project_config.config["projects"]:
            past_bump = SemVer.NO_CHANGE
            current_bump = SemVer.NO_CHANGE
            commits = self.scm.find_new_commits(
                self.scm.development_branch,
                self.scm.stable_branch,
                project["path"]
            )
            for commit in commits:
                next_bump = ConventionalCommits.get_bump_type(commit.message)
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
            self.projects_semver_objects[project["path"]].update_version_files(
                self.projects_semver_objects[project["path"]]._read_default_version_file(version_type="dev")
            )
            changed_projects.append(project['path'])
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
