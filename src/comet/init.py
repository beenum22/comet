import logging
import ast

from .config import ConfigParser
from .scm import Scm
from .conventions import ConventionalCommits


logger = logging.getLogger(__name__)


class InitRepo(object):

    GIT_NOTES_PREFIX: str = "comet"

    def __init__(
            self,
            repo_config_path,
            repo_local_path: str = "./",
            git_notes_state_backend: bool = False,
            push_changes: bool = False
    ):
        self.repo_config_path = repo_config_path
        self.repo_local_path = repo_local_path
        self.git_notes_state_backend = git_notes_state_backend
        self.push_changes = push_changes
        self.config_object = None
        # self.config_object = config_object
        self.scm_object = None
        # self.scm_object = scm_object
        # if not self.config_object:
        self.config_object = ConfigParser(config_path=self.repo_config_path, skip_state=self.git_notes_state_backend)

    def _set_scm_object(self) -> None:
        if not self.scm_object:
            self.scm_object = Scm(
                repo=self.config_object.config["repo"],
                workspace=self.config_object.config["workspace"],
                repo_local_path=self.repo_local_path,
                configure_remote=self.push_changes
            )

    def _interactive_init_repo_info(self) -> None:
        self.config_object.config["workspace"] = input(
            "Enter the name of the SCM provider workspace/userspace[beenum22]: ") or "beenum22"
        self.config_object.config["repo"] = input("Enter the name of the repository[comet]: ") or "comet"

    def _interactive_init_repo_strategy(self) -> None:
        self.config_object.config["strategy"] = {}
        self.config_object.config["strategy"]["development_model"] = {}
        self.config_object.config["strategy"]["development_model"]["type"] = input(
            "Select workflow development model (gitflow/tbd) [gitflow]: ") or "gitflow"
        self.config_object.config["strategy"]["development_model"]["options"] = {}
        if self.config_object.config["strategy"]["development_model"]["type"] == "gitflow":
            self.config_object.config["strategy"]["development_model"]["options"]["stable_branch"] = input(
                "Enter the name of the stable branch[main]: ") or "main"
            self.config_object.config["strategy"]["development_model"]["options"]["development_branch"] = input(
                "Enter the name of the development branch[develop]: ") or "develop"
            self.config_object.config["strategy"]["development_model"]["options"]["release_branch_prefix"] = input(
                "Enter the prefix for release branches[release]: ") or "release"
        self.config_object.config["strategy"]["commits_format"] = {}
        self.config_object.config["strategy"]["commits_format"]["type"] = input(
            "Select commit messages format type [conventional_commits]: ") or "conventional_commits"
        self.config_object.config["strategy"]["commits_format"]["options"] = {}

    def _interactive_init_repo_projects(self) -> None:
        self.config_object.config["projects"] = []
        while True:
            subprojects = input("Do you have sub-projects in the repository?(yes/no)[no]: ") or "no"
            if subprojects not in ["yes", "no"]:
                continue
            subprojects_info = {}
            if subprojects == "no":
                if len(self.config_object.config["projects"]) == 0:
                    subprojects_info["path"] = "."
                    subprojects_info["version"] = "0.0.0"
                    subprojects_info["history"] = {
                        "next_release_type": "",
                        "latest_bump_commit_hash": ""
                    }
                    subprojects_info["version_regex"] = ""
                    subprojects_info["version_files"] = []
                    self.config_object.config["projects"].append(subprojects_info)
                break
            if subprojects == "yes":
                subprojects_info["path"] = input("Enter the path for sub-project: ")
                subprojects_info["history"] = {
                    "next_release_type": "",
                    "latest_bump_commit_hash": ""
                }
                subprojects_info["version"] = input("Enter the version for sub-project[0.0.0]: ") or "0.0.0"
                subprojects_info["version_regex"] = input("Enter the version regex for sub-project[]: ") or ""
                subprojects_info["version_files"] = []
                while True:
                    add_version_files = input(
                        "Include a version file in the sub-project?(yes/no)[no]: ") or "no"
                    if add_version_files not in ["yes", "no"]:
                        continue
                    elif add_version_files == "yes":
                        subprojects_info["version_files"].append(
                            input("Enter the version file path relative to the sub-project?[]: ")
                        )
                    elif add_version_files == "no":
                        break
            self.config_object.config["projects"].append(subprojects_info)

    def _init_repo_info(self, workspace: str, repo: str) -> None:
        self.config_object.config["workspace"] = workspace
        self.config_object.config["repo"] = repo

    def _init_repo_strategy(self, strategy: dict) -> None:
        self.config_object.config["strategy"] = strategy

    def _init_repo_projects(self, projects: list) -> None:
        self.config_object.config["projects"] = projects

    def _is_config_initialized(self) -> bool:
        if not self.config_object.has_config_file():
            logging.debug(f"Comet configuration file is not initialized at [{self.repo_config_path}]")
            return False
        return True

    def _is_state_initialized(self) -> bool:
        state_ref = f"{self.GIT_NOTES_PREFIX}/state/{self.scm_object.get_active_branch()}"
        if not self.scm_object.has_local_reference(reference=state_ref):
            logging.debug(f"Comet versioning state/history is not initialized at [{state_ref}]")
            return False
        return True

    def initialize_config(
            self,
            strategy: dict = {},
            workspace: str = None,
            repo: str = None,
            projects: list = [],
            interactive: bool = True
    ) -> None:
        """
        Initializes the Comet configuration file using method parameters or user inputs if the parameter is not
        specified.

        :param strategy: Development strategy for Comet-managed repository
        :param workspace: Git Username/Workspace of Comet-managed repository
        :param repo: Git Repository name
        :param projects: List of projects managed by Comet in the repository
        :param interactive: Flag to set interactive initialization mode
        :return: None
        :raises AssertionError:
            raises an exception if validation for the initialized Comet configuration file fails
        """
        try:
            assert not self._is_config_initialized(), f"Comet configuration is already initialized at [{self.repo_config_path}]"
            if interactive:
                self._interactive_init_repo_info()
                self._interactive_init_repo_strategy()
                self._interactive_init_repo_projects()
            else:
                assert repo and workspace and len(strategy) > 0 and len(projects) > 0, \
                    f"Please provide all the required parameters for Comet initialization in non-interactive mode " \
                    f"[repo: {repo}, workspace: {workspace}, strategy: {strategy}, projects: {projects}]"
                self._init_repo_info(workspace, repo)
                self._init_repo_strategy(strategy)
                self._init_repo_projects(projects)

            self.config_object.validate_config()
            self._set_scm_object()
            if self.git_notes_state_backend:
                state = State(
                    self.config_object,
                    self.scm_object
                )
                if self._is_state_initialized():
                    logger.warning(
                        f"Some Comet versioning state/history is already initialized at [{self.repo_config_path}]")
                    if state.get_state(
                            f"{self.GIT_NOTES_PREFIX}/state/{self.scm_object.get_active_branch()}",
                            self.scm_object.get_active_branch()
                    ) != self.config_object.config["projects"]:
                        logger.warning(
                            f"The existing version state/history at "
                            f"[{self.GIT_NOTES_PREFIX}/state/{self.scm_object.get_active_branch()}] "
                            f"is deviating from the initialized state. Overriding the state with newer state.")
                state.create_state(
                    self.config_object.config["projects"],
                    f"{self.GIT_NOTES_PREFIX}/state/{self.scm_object.get_active_branch()}",
                    self.scm_object.get_active_branch()
                )

            self.config_object.write_config()
            self.scm_object.commit_changes(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                self.repo_config_path,
                push=self.push_changes,
                add=True
            )
        except Exception as err:
            logger.debug(err)
            raise


class State(object):

    GIT_NOTES_PREFIX: str = "comet"

    def __init__(
            self,
            config_object: ConfigParser,
            scm_object: Scm
    ):
        self.config_object = config_object
        self.scm_object = scm_object

    def has_state(self, state_ref: str) -> bool:
        """
        Check if Comet-managed projects' versioning state is stored in Git notes.

        :return: 'True' if versioning state is found in repository Git notes or 'False' otherwise.
        """
        # try:
        if not self.scm_object.has_local_reference(reference=state_ref):
            # logger.warning(
            #     f"Comet version history/state for reference [{state_ref}] doesn't exist in the local "
            #     f"repository Git notes. Maybe your projects history/state is stored in the project "
            #     f"configuration file instead?")
            return False

        notes_list = self.scm_object.list_notes(
            note_ref=state_ref
        )

        if len(notes_list) == 0:
            logger.warning(
                f"Projects version history/state for [{state_ref}] doesn't exist in the local repository "
                f"Git notes. Please make sure a valid versioning state is provided.")
            return False
        return True
        # except AssertionError as err:
        #     logger.debug(err)
        #     return False

    def get_state(self, state_ref: str, object_ref: str) -> list:
        reference_state_notes_list = self.scm_object.list_notes(
            note_ref=state_ref
        )
        assert len(reference_state_notes_list) > 0, \
            f"Projects version history/state for reference [{state_ref}] doesn't exist in the " \
            f"local repository Git notes. Please make sure a valid versioning state reference is provided."
        # state_notes_objects = [note.split(" ")[1] for note in reference_state_notes_list.split("\n")]
        latest_note = self.scm_object.find_latest_note(state_ref)
        state = ast.literal_eval(
            self.scm_object.read_note(
                note_ref=state_ref,
                object_ref=latest_note
            )
        )
        logger.debug(f"Latest version history/state is successfully fetched for reference [{state_ref}] in the "
                     f"local repository Git notes")
        return state

    def create_state(
            self,
            projects: list,
            state_ref: str,
            object_ref: str
    ) -> None:
        """
        Update versioning state for Comet-managed projects

        :return:
        """
        try:
            assert not self.scm_object.has_local_reference(reference=state_ref), \
                f"Git local notes reference [{state_ref}] for projects' versioning state/history already exists"
            logger.debug(f"Creating projects' version history for [{object_ref}] branch at [{state_ref}] Git notes ref")
            projects_state = []
            for project in projects:
                projects_state.append(
                    {
                        "path": project["path"],
                        "version": project["version"],
                        "history": project["history"]
                    }
                )
            self.scm_object.add_note(
                note_ref=state_ref,
                notes=str(projects_state),
                object_ref=object_ref
            )
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to create Comet-managed projects' versioning state in Git notes")

    def update_state(
            self,
            projects: list,
            state_ref: str,
            object_ref: str
    ) -> None:
        """
        Update versioning state for Comet-managed projects

        :return:
        """
        try:
            assert self.scm_object.has_local_reference(reference=object_ref), \
                f"Git local reference [{object_ref}] for projects' versioning state/history does not exist"
            logger.debug(f"Updating projects' version history for [{object_ref}] branch at [{state_ref}] Git notes ref")
            projects_state = []
            for project in projects:
                projects_state.append(
                    {
                        "path": project["path"],
                        "version": project["version"],
                        "history": project["history"]
                    }
                )
            self.scm_object.add_note(
                note_ref=state_ref,
                notes=str(projects_state),
                object_ref=object_ref
            )
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to update Comet-managed projects' versioning state in Git notes")

    def prepare_config(self) -> None:
        assert self.config_object.has_config_file(), \
            f"Comet configuration is not initialized at [{self.config_object.config_path}]"
        self.config_object.read_config()
        state_ref = f"{self.GIT_NOTES_PREFIX}/state/{self.scm_object.get_active_branch()}"
        assert self.scm_object.has_local_reference(reference=state_ref), \
            f"Comet projects' versioning state/history doesn't exist at Git local reference [{state_ref}]"
