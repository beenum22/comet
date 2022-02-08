import logging
import yaml
from yaml.loader import SafeLoader
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import os

from .utilities import CometUtilities, CometDeprecationContext

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

    :cvar SUPPORTED_STRATEGIES: Supported development work flows for Comet-managed projects
    :cvar SUPPORTED_CONFIG_SCHEMA: Supported configuration file schema for Comet-managed projects
    """

    SUPPORTED_STRATEGIES: list = [
        "gitflow",
        "tbd",
        "custom"
    ]

    DEPRECATED_PARAMETERS: list = [
        "dev_version",
        "stable_version"
    ]

    SUPPORTED_CONFIG_SCHEMA: dict = {
        "type": "object",
        "required": [
            "strategy",
            "repo",
            "workspace",
            "projects"
        ],
        "if": {
            "properties": {
                "strategy": {
                    "type": "string"
                }
            }
        },
        "then": {
            "properties": {
                "strategy": {
                    "enum": [
                        "gitflow",
                        "tbd",
                        "custom"
                    ]
                }
            },
            "required": [
                "strategy",
                "repo",
                "workspace",
                "projects",
                "stable_branch",
                "development_branch",
                "release_branch_prefix",
            ]
        },
        "else": {
            "properties": {
                "strategy": {
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "gitflow",
                                "tbd",
                                "custom"
                            ]
                        },
                        "options": {
                            "type": [
                                "object",
                                "null"
                            ],
                            "properties": {
                                "stable_branch": {
                                    "type": "string"
                                },
                                "development_branch": {
                                    "type": "string"
                                },
                                "release_branch_prefix": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "if": {
                        "properties": {
                            "type": {
                                "const": "gitflow"
                            }
                        }
                    },
                    "then": {
                        "required": [
                            "options"
                        ],
                        "properties": {
                            "options": {
                                "type": "object",
                                "required": [
                                    "stable_branch",
                                    "development_branch",
                                    "release_branch_prefix",
                                ]
                            }
                        }
                    }
                }
            }
        },
        "properties": {
            "strategy": {
                "type": [
                    "object",
                    "string"
                ]
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
                    "oneOf": [
                        {
                            "required": [
                                "stable_version",
                                "dev_version"
                            ]
                        },
                        {
                            "required": [
                                "version",
                                "history"
                            ]
                        }
                    ],
                    "required": [
                        "version_regex",
                        "path",
                        "version_files"
                    ],
                    "properties": {
                        "version": {
                            "type": "string"
                        },
                        "history": {
                            "type": "object",
                            "properties": {
                                "next_release_type": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                },
                                "latest_bump_commit_hash": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                }
                            }
                        },
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

    def _print_deprecated_parameters_warnings(self) -> None:
        if self.has_deprecated_versioning_format():
            logger.deprecated(
                f"Deprecated versioning format is configured for the Comet-managed projects that uses "
                f"'dev_version' and 'stable_version' parameters. These parameters have been deprecated in "
                f"of just 'version' parameter which relies additional 'history' parameter."
            )
        if type(self._lookup_parameter_value("strategy")) is str:
            logger.deprecated(
                f"'strategy' parameter of type 'str' has been deprecated in favor of 'strategy' parameter of type "
                f"'dict'. This new 'strategy' parameter format provides support for setting selected strategy type "
                f"and its additional configured options. "
            )

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
            logger.debug("Comet configuration schema successfully validated")
        except ValidationError as err:
            logger.debug(err)
            raise Exception(f"Comet configuration Schema validation failed. {err.message}")

    @CometUtilities.deprecated_function_warning
    def _validate_version_type(self, version_type: str) -> None:
        """
        Validates the requested version type according to the supported version types specified in
        :cvar::`supported_version_types`.

        :return: None
        :raises AssertionError: raises an exception if unsupported version type is provided
        """
        try:
            supported_version_types: list = [
                "stable",
                "dev"
            ]
            assert version_type in supported_version_types, \
                f"Invalid version type is specified. " \
                f"Supported values are [{','.join(supported_version_types)}]"
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to validate the requested version type [{version_type}]")

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
        self._validate_config_schema()
        self._print_deprecated_parameters_warnings()
        # TODO: Remove
        # self._validate_supported_values()

    # TODO: Refine this method or remove if not needed
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
        try:
            # TODO: Remove redundant config validation line
            # self._validate_config()
            assert project_path in [project_dict["path"] for project_dict in self.config["projects"]], \
                f"The requested Comet project [{project_path}] does not exist in the Comet configuration. " \
                f"Please add the project to the Comet configuration file first."
        except AssertionError as err:
            raise Exception(err)

    def _lookup_parameter_value(self, parameter: str) -> [str, int, list, dict, None]:
        """
        Lookups a specified Comet parameter value in the Comet configuration file.

        :param parameter: Comet parameter name in the Comet configuration file
        :return: Comet parameter value
        """
        try:
            return self.config[parameter]
        except KeyError as err:
            raise Exception(f"The requested Comet parameter [{parameter}] does not exist in Comet config")

    def _lookup_project_parameter_value(self, project_path: str, parameter: str) -> [str, int, list, dict, None]:
        """
        Lookups a specified Comet parameter value for the requested project in the Comet configuration file.

        :param project_path: Comet managed project path in the Comet configuration file
        :param parameter: Comet parameter name for the project in the Comet configuration file
        :return: Comet managed project parameter value
        """
        try:
            self._validate_project_path(project_path)
            for project_dict in self.config["projects"]:
                if project_dict["path"] == project_path:
                    return project_dict[parameter]
        except KeyError as err:
            raise Exception(f"The requested Comet parameter [{parameter}] does not exist in Comet configuration")

    @CometUtilities.unstable_function_warning
    def _change_project_parameter_value(self, project_path: str, parameter: str, value: str) -> None:
        """
        Lookups a specified Comet parameter value for the requested project in the Comet configuration file.

        :param project_path: Comet managed project path in the Comet configuration file
        :param parameter: Comet parameter name for the project in the Comet configuration file
        :param value: Comet parameter value for the project in the Comet configuration file
        :return: Comet managed project parameter value
        """
        try:
            for idx, project_dict in enumerate(self.config["projects"]):
                if project_dict["path"] == project_path:
                    self.config["projects"][idx][parameter] = value
            self.write_config()
        except AssertionError as err:
            logger.debug(err)
            raise Exception(
                f"Failed to update the requested Comet parameter [{parameter}] value for the project "
                f"[{project_path}] in Comet configuration"
            )

    @CometUtilities.deprecated_function_warning
    def _lookup_project_version(self, project_path: str, version_type: [str, None] = None) -> str:
        """
        Lookups a specified reference type version for a specified project from Comet configuration file.

        :param project_path: Project directory path in a Comet-managed repository/directory
        :param version_type:
            Reference version type to lookup for the project in the Comet configuration (Deprecated)
        :return: Project version according to the specified reference version type
        """
        try:
            for project_dict in self.config["projects"]:
                if project_dict["path"] == project_path:
                    return project_dict[f"{version_type}_version" if version_type else "version"]
        except KeyError as err:
            key = f"{version_type}_version" if version_type else "version"
            raise Exception(f"The requested version parameter [{key}] does not exist in Comet config")

    # TODO: Upgrade for new formatting as well.
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
                            subprojects_info["version"] = "0.0.0"
                            subprojects_info["history"] = {
                                "next_release_type": "",
                                "latest_bump_commit_hash": ""
                            }
                            subprojects_info["version_regex"] = ""
                            subprojects_info["version_files"] = []
                            self.config["projects"].append(subprojects_info)
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

    @CometUtilities.deprecation_facilitation_warning
    def has_deprecated_versioning_format(self) -> bool:
        """
        Returns true if the deprecated versioning format is configured where 'dev_version' and 'stable_version'
        parameters are configured for any Comet-managed project.

        :return:
            Returns the 'True' if the deprecated versioning format is configured or 'False' otherwise
        """
        for project in self.config["projects"]:
            if "dev_version" in project or "stable_version" in project:
                return True
        return False

    @CometUtilities.unsupported_function_error
    def has_deprecated_config_parameter(self, deprecated_param: str) -> bool:
        """
        Checks if the provided parameter :param:`deprecated_param` is configured in the Comet configuration file.

        :param deprecated_param: Deprecated parameter to lookup in Comet configuration file
        :return:
            Returns `True` if the deprecated parameter exists in the Comet configuration or `False`
            otherwise
        """
        if deprecated_param in self.config:
            return True
        for project in self.config["projects"]:
            if deprecated_param in project:
                return True
        return False

    def get_projects(self):
        """
        Gets the names for all Comet-managed projects.

        :return: list
        :raises Exception:
            raises an exception if it fails to write to the YAML-based Comet configuration file
        """
        try:
            assert self.config, f"Please load the YAML configuration file first [{self.config_path}]"
            projects = []
            for idx, project_dict in enumerate(self.config["projects"]):
                projects.append(project_dict["path"].lstrip('/.'))
            return projects
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to get project names from the YAML configuration file")

    @CometUtilities.unsupported_function_error
    def get_project_last_bump_type(self, project_path: str) -> [str, None]:
        """
        Fetches the last version bump type for the specified Comet-managed project in :param:`project_path`.

        :param project_path: Project in the Comet configuration file
        :return: Comet-managed project last version bump type specified in 'history' parameter
        :raises Exception: If an invalid project path is specified
        """
        try:
            self._validate_project_path(project_path)
            return self._lookup_project_parameter_value(project_path, "history")["next_release_type"]
        except Exception as err:
            logger.debug(err)
            raise Exception(f"Failed to get the last project [{project_path}] version bump type history from "
                            f"the Comet configuration file")

    @CometUtilities.unsupported_function_error
    def get_project_last_bump_commit_hash(self, project_path: str) -> [str, None]:
        """
        Fetches the last version bump commit hash for the specified Comet-managed project in
        :param:`project_path`.

        :param project_path: Project in the Comet configuration file
        :return: Comet-managed project last version bump commit hash specified in 'history' parameter
        :raises Exception: If an invalid project path is specified
        """
        try:
            self._validate_project_path(project_path)
            return self._lookup_project_parameter_value(project_path, "history")["latest_bump_commit_hash"]
        except Exception as err:
            logger.debug(err)
            raise Exception(f"Failed to get the last project [{project_path}] version bump commit "
                            f"history from the Comet configuration file")

    @CometUtilities.unstable_function_warning
    def get_project_history(self, project_path: str) -> [dict, None]:
        """
        Fetches the version history for the specified Comet-managed project in :param:`project_path`.

        :param project_path: Project in the Comet configuration file
        :return: Comet-managed project latest version history specified in 'history' parameter
        :raises Exception: If an invalid project path is specified
        """
        try:
            self._validate_project_path(project_path)
            return self._lookup_project_parameter_value(project_path, "history")
        except Exception as err:
            logger.debug(err)
            raise Exception(f"Failed to get the last project [{project_path}] version bump commit "
                            f"history from the Comet configuration file")

    # TODO: Remove this method
    @CometUtilities.unsupported_function_error
    def get_project_release_hash(self, project_path: str) -> [str, None]:
        """
        Fetches the release commit hash for the specified Comet-managed project in :param:`project_path`.

        :param project_path: Project in the Comet configuration file
        :return: Comet-managed project release commit hash
        :raises Exception: If an invalid project path is specified
        """
        try:
            self._validate_project_path(project_path)
            return self._lookup_project_parameter_value(
                project_path, "release_commit_sha"
            )
        except (Exception) as err:
            logger.debug(err)
            raise Exception(f"Failed to get the project [{project_path}] release commit hash from the "
                            f"Comet configuration file")

    @CometUtilities.unstable_function_warning
    def get_strategy_type(self) -> str:
        """
        Fetches the configured strategy name.

        :return: Configured strategy name
        """
        if type(self._lookup_parameter_value("strategy")) is str:
            return self._lookup_parameter_value("strategy")
        return self._lookup_parameter_value("strategy")["type"]

    @CometUtilities.unstable_function_warning
    def get_strategy_options(self) -> dict:
        """
        Fetches the configured strategy specific options map.

        :return: Strategy specific configured options
        """
        options = {}
        if type(self._lookup_parameter_value("strategy")) is str:
            with CometDeprecationContext(
                f"Setting strategy options for the deprecated 'strategy' parameter type"
            ):
                options["stable_branch"] = self._lookup_parameter_value("stable_branch")
                options["development_branch"] = self._lookup_parameter_value("development_branch")
                options["release_branch_prefix"] = self._lookup_parameter_value("release_branch_prefix")
        else:
            options = self._lookup_parameter_value("strategy")["options"]
        return options

    @CometUtilities.deprecated_arguments_warning("version_type")
    def get_project_version(self, project_path: str, version_type: [str, None] = None) -> str:
        """
        Fetches the specified version type in :param:`version_type` for the specified project in :param:`project_path`.

        :param project_path: Project in the Comet configuration file
        :param version_type: Reference version type in the Comet configuration file (Deprecated)
        :return: Project specific version according to the specified version type
        :raises Exception:
            raises an exception if an invalid version type is specified
        """
        try:
            if version_type:
                with CometDeprecationContext(
                    f"Validating the version type in deprecated versioning format. Deprecated versioning format has "
                    f"two parameters, 'dev_version' and 'stable_version'."
                ):
                    self._validate_version_type(version_type)
            self._validate_project_path(project_path)
            return self._lookup_project_parameter_value(
                project_path, f"{version_type}_version" if version_type else "version"
            )
        except Exception as err:
            logger.debug(err)
            raise Exception(f"Failed to get the project [{project_path}] version from the Comet configuration file")

    @CometUtilities.deprecated_arguments_warning("version_type")
    def update_project_version(self, project_path: str, version: str, version_type: [str, None] = None) -> None:
        """
        Updates specified version type :param:`version_type` for the specified project :param:`project_path` according
        to the specified version :param:`version` in the Comet configuration file.

        :param project_path: Project in the Comet configuration file
        :param version: Version to set in the Comet configuration file
        :param version_type: Reference version type in the Comet configuration file (Deprecated)
        :return: None
        :raises Exception:
            raises an exception if an invalid version type is specified or specified project doesn't exist
        """
        try:
            if version_type:
                with CometDeprecationContext(
                        f"Validating the version type in deprecated versioning format. Deprecated versioning format has "
                        f"two parameters, 'dev_version' and 'stable_version'."
                ):
                    self._validate_version_type(version_type)
            self._validate_project_path(project_path)
            self._change_project_parameter_value(
                project_path,
                f"{version_type}_version" if version_type else "version",
                version
            )
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to update the project [{project_path}] version in the Comet configuration "
                            f"file")

    @CometUtilities.unstable_function_warning
    def update_project_history(
            self,
            project_path: str,
            bump_type: str = "",
            commit_sha: str = "") -> None:
        """
        Updates last version bump history for the specified Comet-managed project :param:`project_path` in the
        Comet configuration file with the new version bump type and commit hash specified in :param:`bump_type`
        and :param:`commit_hash` respectively.

        :param project_path: Project in the Comet configuration file
        :param bump_type: Last version bump type to set in the Comet configuration file
        :param commit_sha: Last version bump commit hash to set in the Comet configuration file
        :return: None
        :raises Exception:
            raises an exception if an invalid version type is specified or specified project doesn't exist
        """
        try:
            self._validate_project_path(project_path)
            history = {
                "next_release_type": bump_type,
                "latest_bump_commit_hash": commit_sha
            }
            self._change_project_parameter_value(
                project_path,
                "history",
                history
            )
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to update the project [{project_path}] version bump history in the Comet "
                            f"configuration file")

    def read_config(self, validate: bool = True, sanitize: bool = True):
        """
        Reads the YAML-based Comet configuration file and stores it as :attr:`config`.

        :param validate:
            Optionally executes configuration validation. Default is set to `True`.
        :param sanitize:
            Optionally executes sanitization/normalization for project paths. Default is set to `True`.
        :return: None
        :raises Exception:
            raises an exception if it fails to read from the YAML-based Comet configuration file
        """
        try:
            assert os.path.exists(self.config_path), \
                f"Unable to find the Comet configuration file [{self.config_path}]"
            with open(self.config_path) as f:
                self.config = yaml.load(f, Loader=SafeLoader)
            if validate:
                self._validate_config()
            if sanitize:
                self._sanitize_config()
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to read the Comet configuration file")

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
            raise Exception(f"Failed to write the Comet configuration file")