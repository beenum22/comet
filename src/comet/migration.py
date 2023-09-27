import logging
from .config import ConfigParser
from .scm import Scm
from .utilities import CometUtilities, CometDeprecationContext

logger = logging.getLogger(__name__)
logging.getLogger("git").setLevel(logging.ERROR)


class MigrationHelper(object):
    """Helper backend to handle all Comet configuration migration related functionalities/features"""
    def __init__(
            self,
            project_config_path: str,
            scm_provider: str = "github",
            connection_type: str = "https",
            username: str = "",
            password: str = "",
            project_local_path: str = "./",
            ssh_private_key_path: str = "~/.ssh/id_rsa",
            push_changes: bool = False
    ):
        self.project_config_path = project_config_path
        self.scm_provider = scm_provider
        self.connection_type = connection_type
        self.username = username
        self.password = password
        self.project_local_path = project_local_path
        self.ssh_private_key_path = ssh_private_key_path
        self.push_changes = push_changes

        self.project_config = ConfigParser(
            config_path=self.project_config_path
        )
        self.project_config.read_config()

        self.scm = Scm(
            scm_provider=self.scm_provider,
            connection_type=self.connection_type,
            username=self.username,
            password=self.password,
            repo=self.project_config.config["repo"],
            workspace=self.project_config.config["workspace"],
            repo_local_path=self.project_local_path,
            ssh_private_key_path=self.ssh_private_key_path,
            configure_remote=self.push_changes
        )

    @CometUtilities.unstable_function_warning
    def migrate_deprecated_config(self) -> bool:
        """
        Migrates deprecated Comet configuration format to the latest format.

        :return: Returns 'True' if migration is performed or 'False' otherwise
        """
        migration = False
        if type(self.project_config.config["strategy"]) is str:
            logger.info(f"Migrating deprecated strategy parameter type from 'string' to a 'dictionary/map' "
                        f"in Comet configuration")
            strategy = self.project_config.config["strategy"]
            self.project_config.config["strategy"] = {}
            self.project_config.config["strategy"]["development_model"] = {}
            self.project_config.config["strategy"]["commits_format"] = {}
            self.project_config.config["strategy"]["development_model"]["type"] = strategy
            self.project_config.config["strategy"]["commits_format"]["type"] = "conventional_commits"
            self.project_config.config["strategy"]["development_model"]["options"] = {}
            self.project_config.config["strategy"]["commits_format"]["options"] = None
            self.project_config.config["strategy"]["development_model"]["options"]["stable_branch"] = \
                self.project_config.config["stable_branch"]
            self.project_config.config["strategy"]["development_model"]["options"]["development_branch"] = \
                self.project_config.config[
                "development_branch"]
            self.project_config.config["strategy"]["development_model"]["options"]["release_branch_prefix"] = \
                self.project_config.config[
                "release_branch_prefix"]
            self.project_config.config.pop("stable_branch", None)
            self.project_config.config.pop("development_branch", None)
            self.project_config.config.pop("release_branch_prefix", None)
            migration = True
        if self.project_config.has_deprecated_versioning_format():
            logger.info(f"Migrating deprecated versioning format to newer versioning format in Comet "
                        f"configuration")
            projects = []
            for project in self.project_config.config["projects"]:
                project["version"] = project["dev_version"]
                project.pop("dev_version", None)
                project.pop("stable_version", None)
                project["history"] = {}
                project["history"]["next_release_type"] = "no_change"
                project["history"]["latest_bump_commit_hash"] = None
                projects.append(project)
            self.project_config.config["projects"] = projects
            migration = True
        if migration:
            self.project_config.validate_config()
            self.project_config.write_config()
            return migration
        else:
            logger.info(f"No deprecated configuration parameters found in Comet configuration. Skipping migration.")
            return migration

    @CometUtilities.unstable_function_warning
    def migrate_state_backend(self):
        try:
            if self.project_config.get_development_model_type() == "gitflow":
                assert self.scm.has_local_branch(
                    self.project_config.get_development_model_options()["development_branch"]), \
                    f"Development branch [{self.project_config.get_development_model_options()['development_branch']}] " \
                    f"does not exist locally. It is a pre-requisite for state migration!"
                assert self.scm.has_local_branch(
                    self.project_config.get_development_model_options()["stable_branch"]), \
                    f"Stable branch [{self.project_config.get_development_model_options()['stable_branch']}] " \
                    f"does not exist locally. It is a pre-requisite for state migration!"
                # target_branch = input(
                #     "Do you want to migrate state for all branches or a specific one? [all/<branch_name>]: ") or "all"
                # if target_branch == "all":
                #     pass
                # else:
                # assert self.scm.has_local_branch(target_branch), "Target branch doesn't exist locally!"

                stable_note_ref = f"comet/state/{self.project_config.get_development_model_options()['stable_branch']}"
                self.scm.checkout_branch(self.project_config.get_development_model_options()["stable_branch"])


                dev_note_ref = f"comet/state/{self.project_config.get_development_model_options()['development_branch']}"

                projects = []
                note_ref = f"comet/state/{self.scm.get_active_branch()}"
                self.project_config.read_config()
                for project in self.project_config.config["projects"]:
                    projects.append(
                        {
                            "path": project["path"],
                            "version": project["version"],
                            "history": project["history"]
                        }
                    )
                self.scm.add_note(
                    note_ref=note_ref,
                    notes=str(projects),
                    object_ref=self.scm.get_active_branch()
                )

                # self.scm.checkout_branch(self.project_config.get_development_model_options["stable_branch"])

            elif self.project_config.get_development_model_type() == "tbd":
                pass
        except Exception as err:
            raise
