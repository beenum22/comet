import logging
import os

from .scm import Scm

logger = logging.getLogger(__name__)


class ChangeLog(object):

    CHANGELOG_FORMAT = {

    }

    def __init__(
            self,
            changelog_format: str = "keepachangelog",
            changelog_file: str = "CHANGELOG",
            project_name: str = "Test",
            project_description: str = f"All notable changes to this project will be documented in this file."
    ):
        self.changelog_format = changelog_format
        self.changelog_file = changelog_file
        self.project_name = project_name
        self.project_description = project_description

    def init_changelog(self):
        logger.info(f"Initializing a changelog file [{self.changelog_file}]")
        with open(self.changelog_file, "w") as f:
            f.write(f"# Changelog\n{self.project_description}\n\n[]## [Unreleased]\n")

    def sanity_check(self) -> None:
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
        if not os.path.exists(self.changelog_file):
            logger.debug(f"Changelog file [{self.changelog_file}] doesn't exist")
            self.init_changelog()

    # def prepare_changelog(self):
