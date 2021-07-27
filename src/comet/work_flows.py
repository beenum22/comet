# from typing import TypedDict, List, Dict
import logging
import os
from .scm import Scm
from .semver import SemVer
from .conventions import ConventionalCommits
from .config import ConfigParser

logger = logging.getLogger(__name__)


# class Project(TypedDict):
#     name: str
#     path: str
#     version_files: List[str]


class GitFlow(object):

    def __init__(
            self,
            connection_type: str = "https",
            scm_provider: str = "bitbucket",
            username: str = "",
            password: str = "",
            ssh_private_key_path: str = "~/.ssh/id_rsa",
            project_local_path: str = "./",
            # projects: Projects = []
            project_config_path: str = "./comet"
    ) -> None:
        self.connection_type = connection_type
        self.scm_provider = scm_provider
        self.username = username
        self.password = password
        self.ssh_private_key_path = ssh_private_key_path
        self.project_config_path = project_config_path
        self.project_local_path = project_local_path
        self.scm = None
        self.project_config = {}
        self.projects_semver_objects = {
            "bgcf": {}
        }
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
            for project in self.project_config.config["projects"]:
                self.projects_semver_objects[project["path"]] = SemVer(
                    project_path=project["path"],
                    version_files=project["version_files"],
                    project_version_file=self.project_config_path
                )
        except Exception:
            raise

    def stable_flow(self):
        logger.warning("Stable branch GitFlow is under-development")
        # logger.info("Executing Stable branch GitFlow")

    def development_flow(self):
        logger.info("Executing Development branch GitFlow")
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
            self.scm.commit_changes(
                f"chore: update comet config and project version files for {project['path']}\n\n[skip ci]",
                project["path"],
                self.project_config_path,
                push=True
            )

