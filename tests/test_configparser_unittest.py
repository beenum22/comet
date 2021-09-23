import unittest
from unittest.mock import patch, mock_open
import logging

from src.comet.config import ConfigParser

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class ConfigParserTest(unittest.TestCase):

    TEST_DEV_VERSION = "0.1.0-dev.2"
    TEST_STABLE_VERSION = "0.1.0"
    TEST_PROJECT_DIRECTORY = "test_project"
    TEST_PROJECT_CONFIG_FILE = ".comet.yml"
    TEST_PROJECT_VERSION_FILE = "VERSION"
    TEST_PROJECT_CONFIG = {
        "strategy": "gitflow",
        "workspace": "ngvoice",
        "repo": "comet",
        "stable_branch": "master",
        "development_branch": "develop",
        "release_branch_prefix": "release",
        "projects": [
            {
                "path": TEST_PROJECT_DIRECTORY,
                "stable_version": TEST_STABLE_VERSION,
                "dev_version": TEST_DEV_VERSION,
                "version_regex": "",
                "version_files": [
                    TEST_PROJECT_VERSION_FILE
                ]
            }
        ]
    }

    def test_initialize_config(
            self
    ):
        logger.info("Executing unit tests for 'ConfigParser.initialize_config' method")

        configparser = ConfigParser(
            config_path=f"test_comet.yml"
        )

        configparser.initialize_config(
            strategy=self.TEST_PROJECT_CONFIG["strategy"],
            workspace=self.TEST_PROJECT_CONFIG["workspace"],
            repo=self.TEST_PROJECT_CONFIG["repo"],
            stable_branch=self.TEST_PROJECT_CONFIG["stable_branch"],
            development_branch=self.TEST_PROJECT_CONFIG["development_branch"],
            release_branch_prefix=self.TEST_PROJECT_CONFIG["release_branch_prefix"],
            projects=self.TEST_PROJECT_CONFIG["projects"]
        )

        logger.debug("Testing initialized test config output")
        self.assertEqual(
            configparser.config,
            self.TEST_PROJECT_CONFIG
        )

        logger.info("Testing initialized test config for unsupported values exception handling")
        with self.assertRaises(Exception) as err:
            configparser.initialize_config(
                strategy="tbd",
                workspace=self.TEST_PROJECT_CONFIG["workspace"],
                repo=self.TEST_PROJECT_CONFIG["repo"],
                stable_branch=self.TEST_PROJECT_CONFIG["stable_branch"],
                development_branch=self.TEST_PROJECT_CONFIG["development_branch"],
                release_branch_prefix=self.TEST_PROJECT_CONFIG["release_branch_prefix"],
                projects=self.TEST_PROJECT_CONFIG["projects"]
            )

        logger.debug("Testing initialized test config for invalid schema exception handling")
        with self.assertRaises(Exception) as err:
            configparser.initialize_config(
                strategy=self.TEST_PROJECT_CONFIG["strategy"],
                workspace=self.TEST_PROJECT_CONFIG["workspace"],
                repo=self.TEST_PROJECT_CONFIG["repo"],
                stable_branch=self.TEST_PROJECT_CONFIG["stable_branch"],
                development_branch=self.TEST_PROJECT_CONFIG["development_branch"],
                release_branch_prefix=self.TEST_PROJECT_CONFIG["release_branch_prefix"],
                projects=[{
                    "project_path": "test_project",
                    "project_version": "1.1.1",
                }]
            )

    def test_get_project_version(self):
        logger.info("Executing unit tests for 'ConfigParser.get_project_version' method")

        configparser = ConfigParser(
            config_path=self.TEST_PROJECT_CONFIG_FILE
        )
        configparser.config = self.TEST_PROJECT_CONFIG

        logger.debug("Testing 'stable' reference version reading")
        self.assertEqual(
            configparser.get_project_version(self.TEST_PROJECT_DIRECTORY, "stable"),
            self.TEST_STABLE_VERSION
        )
        logger.debug("Testing 'dev' reference version reading")
        self.assertEqual(
            configparser.get_project_version(self.TEST_PROJECT_DIRECTORY, "dev"),
            self.TEST_DEV_VERSION
        )

    @patch('builtins.open', new_callable=mock_open)
    def test_update_project_version(
            self,
            mock_update
    ):
        logger.info("Executing unit tests for 'ConfigParser.update_project_version' method")
        configparser = ConfigParser(
            config_path=self.TEST_PROJECT_CONFIG_FILE
        )
        configparser.config = self.TEST_PROJECT_CONFIG

        configparser.update_project_version(self.TEST_PROJECT_DIRECTORY, "0.2.0", "stable")
        configparser.update_project_version(self.TEST_PROJECT_DIRECTORY, "0.2.0-dev.1", "dev")

        logger.debug("Testing 'stable' reference version update")
        self.assertEqual(
            configparser.get_project_version(self.TEST_PROJECT_DIRECTORY, "stable"),
            "0.2.0"
        )

        logger.debug("Testing 'dev' reference version update")
        self.assertEqual(
            configparser.get_project_version(self.TEST_PROJECT_DIRECTORY, "dev"),
            "0.2.0-dev.1"
        )

        logger.debug("Testing file update call")
        mock_update.assert_called_with(configparser.config_path, 'w')

    @patch('src.comet.config.os')
    @patch('builtins.open', new_callable=mock_open, read_data=str(TEST_PROJECT_CONFIG))
    def test_read_config(
            self,
            mock_read,
            mock_os
    ):
        logger.info("Executing unit tests for 'ConfigParser.read_config' method")

        logger.debug("Testing configuration file read without sanitization")
        configparser = ConfigParser(
            config_path=self.TEST_PROJECT_CONFIG_FILE
        )
        configparser.read_config(sanitize=False)

        logger.debug("Testing file read call")
        mock_read.assert_called_with(configparser.config_path)

        logger.debug("Testing read data from the file")
        self.assertEqual(
            configparser.config,
            self.TEST_PROJECT_CONFIG
        )

        logger.debug("Testing incorrect configuration file path exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path="test_read_file"
            )
            mock_read.side_effect = Exception()
            configparser.read_config(sanitize=False)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_config(
            self,
            mock_update
    ):
        logger.info("Executing unit tests for 'ConfigParser.write_config' method")

        logger.debug("Testing configuration file read without sanitization")
        configparser = ConfigParser(
            config_path=self.TEST_PROJECT_CONFIG_FILE
        )

        configparser.config = self.TEST_PROJECT_CONFIG

        configparser.write_config()

        logger.debug("Testing file update call")
        mock_update.assert_called_with(configparser.config_path, 'w')

        logger.debug("Testing file update exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path="test_read_file"
            )
            configparser.config = self.TEST_PROJECT_CONFIG
            mock_update.side_effect = Exception()
            configparser.write_config()


if __name__ == '__main__':
    unittest.main()