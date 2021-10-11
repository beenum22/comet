import logging
import yaml
from yaml.loader import SafeLoader
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import os

from .utilities import CometUtilities

logger = logging.getLogger(__name__)


class ConfigParser(object):
    """
    Backend to handle YAML-based Comet project configuration file.

    This ConfigParser backend handles all parsing operations related to Comet-specific project configuration file.
    This backend provides support to perform the following operations:
        * Initialize configuration file in interactive mode
        * Read from configuration file
        * Write changes to the configuration file
        * Validate configuration file schema

    .. important::
        Current limitation:
            * Comet must be executed from the root directory on the Comet-managed repositories
            * Comet-managed repositories must have `.comet.yml` at the root directory

    Example:

    .. code-block:: python

        project_config = ConfigParser(
            config_path=args.project_config
        )

    :cvar SUPPORTED_WORKFLOWS: Supported development work flows for Comet-managed projects
    :cvar SUPPORTED_VERSION_TYPES: Supported reference version types for Comet-managed projects
    :cvar SUPPORTED_CONFIG_SCHEMA: Supported configuration file schema for Comet-managed projects
    """

    SUPPORTED_WORKFLOWS: list = [
        "gitflow"
    ]

    SUPPORTED_VERSION_TYPES: list = [
        "stable",
        "dev"
    ]

    SUPPORTED_CONFIG_SCHEMA: dict = {
        "type": "object",
        "required": [
            "strategy",
            "repo",
            "workspace",
            "stable_branch",
            "development_branch",
            "release_branch_prefix",
            "projects"
        ],
        "properties": {
            "strategy": {
                "type": "string"
            },
            "repo": {
                "type": "string"
            },
            "workspace": {
                "type": "string"
            },
            "stable_branch": {
                "type": "string"
            },
            "development_branch": {
                "type": "string"
            },
            "release_branch_prefix": {
                "type": "string"
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "stable_version",
                        "dev_version",
                        "version_regex",
                        "path",
                        "version_files"
                    ],
                    "properties": {
                        "stable_version": {
                            "type": "string"
                        },
                        "dev_version": {
                            "type": "string"
                        },
                        "version_regex": {
                            "type": "string"
                        },
                        "path": {
                            "type": "string"
                        },
                        "version_files": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                    }
                }
            }
        }
    }

    def __init__(
            self,
            config_path: str = ".comet.yml",
    ) -> None:
        """
        Initialize a new ConfigParser class object.

        :param config_path: Comet-managed project configuration file
        :return: None
        """
        self.config_path: str = config_path
        self.config: dict = {}

    def _validate_config_schema(self) -> None:
        """
        Validates the Comet-managed project configuration file schema according to the supported schema provided by
        :cvar:`SUPPORTED_CONFIG_SCHEMA`.

        :return: None
        :raises ValidationError:
            raises an exception if the configuration schema validation fails
        """
        try:
            validate(instance=self.config, schema=self.SUPPORTED_CONFIG_SCHEMA)
            logger.debug("YAML configuration schema successfully validated")
        except ValidationError as err:
            raise Exception(f"YAML Configuration Schema validation failed. {err.message}")

    def _validate_supported_values(self) -> None:
        """
        Validates that the supported values for Comet-managed project configuration parameters are provided.

        :return: None
        :raises AssertionError:
            raises an exception if unsupported configuration file parameter values are provided
        """
        assert self.config["strategy"] in self.SUPPORTED_WORKFLOWS, \
            f"Unsupported work flow strategy [{self.config['strategy']}] is requested. " \
            f"Supported work flows are [{','.join(self.SUPPORTED_WORKFLOWS)}]"

    def _validate_config(self) -> None:
        """
        Executes all the Comet-managed project configuration file validation operations. Currently, it checks the
        following:
            * Configuration file YAML output existence
            * Schema validation
            * Supported values validation.

        :return: None
        :raises AssertionError, ValidationError:
            raises an exception if any type of configuration file validation fails
        """
        assert self.config, "No YAML configuration found! Please read the configuration file first."
        self._validate_config_schema(), "YAML configuration schema validation failed!"
        self._validate_supported_values()

    # TODO: Add repository directory path if Comet is executed from a different directory
    @CometUtilities.unstable_function_warning
    def _sanitize_config(self) -> None:
        """
        Sanitizes/Normalizes all the file/directory paths found in a Comet-managed project configuration file.

        For example:

            Repo directory structure:
                test_repo/
                    --> muneeb/
                    --> .comet.yml


            Project Path = 'muneeb/

        :return: None
        :raises AssertionError, ValidationError:
            raises an exception if any type of configuration file validation fails
        """
        self._validate_config()
        logger.debug(
            f"Sanitizing project configuration according to the root/repo directory [{os.path.dirname(self.config_path)}]")
        for idx, project in enumerate(self.config["projects"]):
            if not project['path'] in [".", "./", ""]:
                self.config["projects"][idx]["path"] = f"{os.path.join(os.path.dirname(self.config_path), project['path'])}"
        logger.debug(f"Sanitized project configuration according to the root/repo directory [{os.path.dirname(self.config_path)}]")

    # TODO: Try to remove configuration data validation
    def _validate_project_path(self, project_path: str) -> None:
        """
        Validates that the requested project exists Comet projects configuration file.

        :param project_path: Project directory path in a Comet-managed repository/directory
        :return: None
        :raises AssertionError:
            raises an exception if the specified project path doesn't exist in the Comet projects configuration file
        """
        self._validate_config()
        assert project_path in [project_dict["path"] for project_dict in self.config["projects"]], \
            f"Project [{project_path}] not found! Please add the project to configuration file first."

    def _lookup_project_version(self, project_path: str, version_type: str = "stable_version") -> str:
        """
        Lookups a specified reference type version for a specified project from Comet configuration file.

        :param project_path: Project directory path in a Comet-managed repository/directory
        :param version_type:
            Reference version type to lookup for the project in the Comet configuration.
            Default is set to "stable_version"
        :return: Project version according to the specified reference version type
        """
        assert version_type in ["stable_version", "dev_version"], \
            f"Incorrect version type [{version_type}] is requested for lookup. " \
            f"Supported values are [{','.join['stable_version', 'dev_version']}]"
        for project_dict in self.config["projects"]:
            if project_dict["path"] == project_path:
                return project_dict[version_type]

    def initialize_config(
            self,
            strategy: str = None,
            workspace: str = None,
            repo: str = None,
            stable_branch: str = None,
            development_branch: str = None,
            release_branch_prefix: str = None,
            projects: list = []
    ) -> None:
        """
        Initializes the Comet configuration file using method parameters or user inputs if the parameter is not
        specified.

        :param strategy: Development strategy for Comet-managed repository
        :param workspace: Git Username/Workspace of Comet-managed repository
        :param repo: Git Repository name
        :param stable_branch: Git stable branch name for Comet-managed repository
        :param development_branch: Git development branch name for Comet-managed repository
        :param release_branch_prefix: Git release branches prefix for Comet-managed repository
        :param projects: List of projects managed by Comet in the repository
        :return: None
        :raises AssertionError:
            raises an exception if validation for the initialized Comet configuration file fails
        """
        try:
            if not strategy:
                self.config["strategy"] = input("Select workflow strategy [gitflow]: ") or "gitflow"
            else:
                self.config["strategy"] = strategy
            if not workspace:
                self.config["workspace"] = input("Enter the name of the SCM provider workspace/userspace [ngvoice]: ") or "ngvoice"
            else:
                self.config["workspace"] = workspace
            if not repo:
                self.config["repo"] = input("Enter the name of the repository[ansible_k8s_ims]: ") or "ansible_k8s_ims"
            else:
                self.config["repo"] = repo
            if not stable_branch:
                self.config["stable_branch"] = input("Enter the name of the stable branch[master]: ") or "master"
            else:
                self.config["stable_branch"] = stable_branch
            if not development_branch:
                self.config["development_branch"] = input("Enter the name of the development branch[develop]: ") or "develop"
            else:
                self.config["development_branch"] = development_branch
            if not release_branch_prefix:
                self.config["release_branch_prefix"] = input("Enter the prefix for release branches[release]: ") or "release"
            else:
                self.config["release_branch_prefix"] = release_branch_prefix
            if not projects:
                self.config["projects"] = []
                while True:
                    subprojects = input("Do you have sub-projects in the repository?(yes/no)[no]: ") or "no"
                    if subprojects not in ["yes", "no"]:
                        continue
                    subprojects_info = {}
                    if subprojects == "no":
                        if len(self.config["projects"]) == 0:
                            subprojects_info["path"] = "."
                            subprojects_info["stable_version"] = "0.0.0"
                            subprojects_info["dev_version"] = "0.0.0-dev.1"
                            subprojects_info["version_regex"] = ""
                            subprojects_info["version_files"] = []
                            self.config["projects"].append(subprojects_info)
                        break
                    if subprojects == "yes":
                        subprojects_info["path"] = input("Enter the path for sub-project: ")
                        subprojects_info["stable_version"] = input("Enter the stable version for sub-project[0.0.0]: ") or "0.0.0"
                        subprojects_info["dev_version"] = input("Enter the dev version for sub-project[0.0.0-dev.1]: ") or "0.0.0-dev.1"
                        subprojects_info["version_regex"] = input("Enter the version regex for sub-project[]: ") or ""
                        subprojects_info["version_files"] = []
                        while True:
                            add_version_files = input("Include a version file in the sub-project?(yes/no)[no]: ") or "no"
                            if add_version_files not in ["yes", "no"]:
                                continue
                            elif add_version_files == "yes":
                                subprojects_info["version_files"].append(
                                    input("Enter the version file path relative to the sub-project?[]: ")
                                )
                            elif add_version_files == "no":
                                break
                    self.config["projects"].append(subprojects_info)
            else:
                self.config["projects"] = projects
            self._validate_config()
        except Exception as err:
            logger.debug(err)
            raise

    def get_projects(self):
        """
        Gets the names for all Comet-managed projects.

        :return: list
        :raises Exception:
            raises an exception if it fails to write to the YAML-based Comet configuration file
        """
        try:
            assert os.path.exists(self.config_path), f"Unable to find the YAML configuration file [{self.config_path}]"
            assert self.config, f"Please load the YAML configuration file first [{self.config_path}]"
            projects = []
            for idx, project_dict in enumerate(self.config["projects"]):
                projects.append(project_dict["path"].lstrip('/.'))
            return projects
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to get project names from the YAML configuration file")

    def get_project_version(self, project_path: str, version_type: str = "stable") -> str:
        """
        Fetches the specified version type in :param:`version_type` for the specified project in :param:`project_path`.

        :param project_path: Project in the Comet configuration file
        :param version_type: Reference version type in the Comet configuration file
        :return: Project specific version according to the specified version type
        :raises Exception:
            raises an exception if an invalid version type is specified
        """
        try:
            assert version_type in ["stable", "dev"], \
                f"Invalid version type is specified. " \
                f"Supported values are [{','.join(['stable', 'dev'])}]"
            self._validate_project_path(project_path)
            return self._lookup_project_version(project_path, version_type=f"{version_type}_version")
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to get {version_type} version from the YAML configuration file")

    def update_project_version(self, project_path: str, version: str, version_type: str = "dev") -> None:
        """
        Updates specified version type :param:`version_type` for the specified project :param:`project_path` according
        to the specified version :param:`version` in the Comet configuration file.

        :param project_path: Project in the Comet configuration file
        :param version: Version to set in the Comet configuration file
        :param version_type: Reference version type in the Comet configuration file
        :return: None
        :raises Exception:
            raises an exception if an invalid version type is specified or specified project doesn't exist
        """
        try:
            self._validate_config()
            assert version_type in ["stable", "dev"], \
                f"Invalid version type is specified. " \
                f"Support values are [{','.join(['stable', 'dev'])}]"
            assert project_path in [project_dict["path"] for project_dict in self.config["projects"]], \
                f"Project [{project_path}] not found! Please add the project to configuration file first."
            for idx, project_dict in enumerate(self.config["projects"]):
                if project_dict["path"] == project_path:
                    self.config["projects"][idx][f"{version_type}_version"] = version
            self.write_config()
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to update version in the YAML configuration file")

    def read_config(self, sanitize=True):
        """
        Reads the YAML-based Comet configuration file and stores it as :attr:`config`.

        :param sanitize:
            Optionally executes sanitization/normalization for project paths. Default is set to `True`.
        :return: None
        :raises Exception:
            raises an exception if it fails to read from the YAML-based Comet configuration file
        """
        try:
            assert os.path.exists(self.config_path), f"Unable to find the YAML configuration file [{self.config_path}]"
            with open(self.config_path) as f:
                self.config = yaml.load(f, Loader=SafeLoader)
            if sanitize:
                self._sanitize_config()
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to read the YAML configuration file")

    def write_config(self):
        """
        Writes the output of :attr:`config` to the YAML-based Comet configuration file.

        :return: None
        :raises Exception:
            raises an exception if it fails to write to the YAML-based Comet configuration file
        """
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, sort_keys=False)
        except Exception as err:
            logger.debug(err)
            raise Exception(f"Failed to write the YAML configuration file")