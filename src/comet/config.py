from typing import List, TypedDict
# from typing_extensions import TypedDict
import logging
import yaml
from yaml.loader import SafeLoader
from schema import Schema, And, Use, Optional, SchemaError
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import os

logger = logging.getLogger(__name__)


# class YamlSchema(TypedDict):
#     name: str
#     path: str
#     version_files: List[str]


class ConfigParser(object):

    SUPPORTED_WORKFLOWS: list = [
        "gitflow"
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
                        "version",
                        "version_regex",
                        "path",
                        "version_files"
                    ],
                    "properties": {
                        "version": {
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
    ):
        self.config_path: str = config_path
        self.config: dict = {}

    def _validate_config_schema(self) -> None:
        try:
            validate(instance=self.config, schema=self.SUPPORTED_CONFIG_SCHEMA)
            logger.debug("YAML configuration schema successfully validated")
        except ValidationError as err:
            raise Exception(f"YAML Configuration Schema validation failed. {err.message}")

    def _validate_supported_values(self) -> None:
        assert self.config["strategy"] in self.SUPPORTED_WORKFLOWS, \
            f"Unsupported work flow strategy [{self.config['strategy']}] is requested. " \
            f"Supported work flows are [{','.join(self.SUPPORTED_WORKFLOWS)}]"

    def _validate_config(self) -> None:
        assert self.config, "No YAML configuration found! Please read the configuration file first."
        self._validate_config_schema(), "YAML configuration schema validation failed!"
        self._validate_supported_values()

    def _sanitize_config(self) -> None:
        self._validate_config()
        logger.debug(
            f"Sanitizing project configuration according to the root/repo directory [{os.path.dirname(self.config_path)}]")
        for idx, project in enumerate(self.config["projects"]):
            self.config["projects"][idx]["path"] = f"{os.path.join(os.path.dirname(self.config_path), project['path'])}"
        logger.debug(f"Sanitized project configuration according to the root/repo directory [{os.path.dirname(self.config_path)}]")

    def initialize_config(self):
        try:
            self.config["strategy"] = input("Select workflow strategy [gitflow]: ") or "gitflow"
            self.config["repo"] = input("Enter the name of the SCM provider workspace/userspace [ngvoice]: ") or "ngvoice"
            self.config["workspace"] = input("Enter the name of the repository[ansible_k8s_ims]: ") or "ansible_k8s_ims"
            self.config["stable_branch"] = input("Enter the name of the stable branch[master]: ") or "master"
            self.config["development_branch"] = input("Enter the name of the development branch[develop]: ") or "develop"
            self.config["release_branch_prefix"] = input("Enter the prefix for release branches[release]: ") or "release"
            self.config["projects"] = []
            while True:
                subprojects = input("Do you have sub-projects in the repository?(yes/no)[no]: ") or "no"
                if subprojects not in ["yes", "no"]:
                    continue
                subprojects_info = {}
                if subprojects == "no" and len(subprojects_info) == 0:
                    subprojects_info["path"] = "."
                    subprojects_info["version"] = "0.1.0"
                    subprojects_info["version_regex"] = ""
                    subprojects_info["version_files"] = []
                if subprojects == "yes":
                    subprojects_info["path"] = input("Enter the path for sub-project: ")
                    subprojects_info["version"] = input("Enter the version for sub-project[0.1.0]: ") or "0.1.0"
                    subprojects_info["version_regex"] = input("Enter the version regex for sub-project[]: ") or ""
                    while True:
                        subprojects_info["version_files"] = []
                        version_files = input("Do you have version files in the sub-project?(yes/no)[no]: ") or "no"
                        if version_files not in ["yes", "no"]:
                            continue
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
                        break
                self.config["projects"].append(subprojects_info)
                break
            self._validate_config()
        except AssertionError as err:
            logger.debug(err)
            raise

    def get_project_version(self, project_path: str) -> str:
        try:
            self._validate_config()
            assert project_path in [project_dict["path"] for project_dict in self.config["projects"]], \
                f"Project [{project_path}] not found! Please add the project to configuration file first."
            for project_dict in self.config["projects"]:
                if project_dict["path"] == project_path:
                    return project_dict["version"]
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to get version from the YAML configuration file")

    def update_project_version(self, project_path: str, version: str) -> None:
        try:
            self._validate_config()
            assert project_path in [project_dict["path"] for project_dict in self.config["projects"]], \
                f"Project [{project_path}] not found! Please add the project to configuration file first."
            for idx, project_dict in enumerate(self.config["projects"]):
                if project_dict["path"] == project_path:
                    self.config["projects"][idx]["version"] = version
            self.write_config()
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to update version in the YAML configuration file")

    def read_config(self, sanitize=False):
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
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, sort_keys=False)
        except AssertionError as err:
            logger.debug(err)
            raise Exception(f"Failed to write the YAML configuration file")