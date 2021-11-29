import unittest
from unittest.mock import patch, mock_open
import logging

from .common import TestBaseConfig
from src.comet.config import ConfigParser

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class ConfigParserTest(unittest.TestCase, TestBaseConfig):

    def test_initialize_config(
            self
    ):
        logger.info("Executing unit tests for 'ConfigParser.initialize_config' method")

        configparser_v0 = ConfigParser(
            config_path=f"test_comet.yml"
        )

        configparser_v1 = ConfigParser(
            config_path=f"test_comet.yml"
        )

        configparser_v0.initialize_config(
            strategy=self.TEST_GITFLOW_CONFIG_V0["strategy"],
            workspace=self.TEST_GITFLOW_CONFIG_V0["workspace"],
            repo=self.TEST_GITFLOW_CONFIG_V0["repo"],
            stable_branch=self.TEST_GITFLOW_CONFIG_V0["stable_branch"],
            development_branch=self.TEST_GITFLOW_CONFIG_V0["development_branch"],
            release_branch_prefix=self.TEST_GITFLOW_CONFIG_V0["release_branch_prefix"],
            projects=self.TEST_GITFLOW_CONFIG_V0["projects"]
        )

        configparser_v1.initialize_config(
            strategy=self.TEST_GITFLOW_CONFIG_V1["strategy"],
            workspace=self.TEST_GITFLOW_CONFIG_V1["workspace"],
            repo=self.TEST_GITFLOW_CONFIG_V1["repo"],
            stable_branch=self.TEST_GITFLOW_CONFIG_V1["stable_branch"],
            development_branch=self.TEST_GITFLOW_CONFIG_V1["development_branch"],
            release_branch_prefix=self.TEST_GITFLOW_CONFIG_V1["release_branch_prefix"],
            projects=self.TEST_GITFLOW_CONFIG_V1["projects"]
        )

        logger.debug("Testing initialized test config with v0/old format")
        self.assertEqual(
            configparser_v0.config,
            self.TEST_GITFLOW_CONFIG_V0
        )

        logger.debug("Testing initialized test config with v1/new format")
        self.assertEqual(
            configparser_v1.config,
            self.TEST_GITFLOW_CONFIG_V1
        )

        logger.info("Testing initialized test config for unsupported values exception handling")
        with self.assertRaises(Exception) as err:
            configparser_v0.initialize_config(
                strategy="tbd",
                workspace=self.TEST_GITFLOW_CONFIG_V0["workspace"],
                repo=self.TEST_GITFLOW_CONFIG_V0["repo"],
                stable_branch=self.TEST_GITFLOW_CONFIG_V0["stable_branch"],
                development_branch=self.TEST_GITFLOW_CONFIG_V0["development_branch"],
                release_branch_prefix=self.TEST_GITFLOW_CONFIG_V0["release_branch_prefix"],
                projects=self.TEST_GITFLOW_CONFIG_V0["projects"]
            )

        logger.debug("Testing initialized test config for invalid schema exception handling")
        with self.assertRaises(Exception) as err:
            configparser_v0.initialize_config(
                strategy=self.TEST_GITFLOW_CONFIG_V0["strategy"],
                workspace=self.TEST_GITFLOW_CONFIG_V0["workspace"],
                repo=self.TEST_GITFLOW_CONFIG_V0["repo"],
                stable_branch=self.TEST_GITFLOW_CONFIG_V0["stable_branch"],
                development_branch=self.TEST_GITFLOW_CONFIG_V0["development_branch"],
                release_branch_prefix=self.TEST_GITFLOW_CONFIG_V0["release_branch_prefix"],
                projects=[{
                    "project_path": "test_project",
                    "project_version": "1.1.1",
                }]
            )

    def test_has_deprecated_config_parameter(self):
        logger.info("Executing unit tests for 'ConfigParser.has_deprecated_config_parameter' method")

        configparser_v0 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0

        configparser_v1 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1

        logger.debug("Testing 'stable_version' deprecated parameter for v0/old config format")
        self.assertTrue(
            configparser_v0.has_deprecated_config_parameter("stable_version")
        )

        logger.debug("Testing 'stable_version' deprecated parameter for v1/new config format")
        self.assertFalse(
            configparser_v1.has_deprecated_config_parameter("stable_version")
        )

    def test_get_projects(self):
        logger.info("Executing unit tests for 'ConfigParser.get_projects' method")

        configparser_v0 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0

        configparser_v1 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1

        logger.debug("Testing 'projects' fetch for v0/old config format")
        self.assertEqual(
            configparser_v0.get_projects(),
            [self.TEST_PROJECT_DIRECTORY]
        )

        logger.debug("Testing 'projects' fetch for v1/new config format")
        self.assertEqual(
            configparser_v1.get_projects(),
            [self.TEST_PROJECT_DIRECTORY]
        )

        logger.debug("Testing projects fetch exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path=f"test_comet.yml"
            )
            configparser.get_projects()

    def test_get_project_history(self):
        logger.info("Executing unit tests for 'ConfigParser.get_project_history' method")
        configparser_v0 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0

        configparser_v1 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1

        logger.debug("Testing 'history' parameter exception handling for v0/old config format")
        with self.assertRaises(Exception):
            configparser_v0.get_project_history(
                configparser_v0.config["projects"][0]["path"]
            )

        logger.debug("Testing 'history' get for v1/new config format")
        self.assertEqual(
            configparser_v1.get_project_history(
                configparser_v1.config["projects"][0]["path"]
            ),
            self.TEST_PROJECT_HISTORY
        )

    def test_get_project_version(self):
        logger.info("Executing unit tests for 'ConfigParser.get_project_version' method")

        configparser_v0 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0

        configparser_v1 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1

        logger.debug("Testing 'stable' reference version read for v0/old config format")
        self.assertEqual(
            configparser_v0.get_project_version(self.TEST_PROJECT_DIRECTORY, "stable"),
            self.TEST_STABLE_VERSION
        )
        logger.debug("Testing 'dev' reference version read for v0/old config format")
        self.assertEqual(
            configparser_v0.get_project_version(self.TEST_PROJECT_DIRECTORY, "dev"),
            self.TEST_DEV_VERSION
        )
        logger.debug("Testing version read for v1/new config format")
        self.assertEqual(
            configparser_v1.get_project_version(self.TEST_PROJECT_DIRECTORY),
            self.TEST_DEV_VERSION
        )

    @patch('builtins.open', new_callable=mock_open)
    def test_update_project_version(
            self,
            mock_update
    ):
        logger.info("Executing unit tests for 'ConfigParser.update_project_version' method")

        configparser_v0 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0

        configparser_v1 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1

        configparser_v0.update_project_version(self.TEST_PROJECT_DIRECTORY, "0.2.0", "stable")
        configparser_v0.update_project_version(self.TEST_PROJECT_DIRECTORY, "0.2.0-dev.1", "dev")
        configparser_v1.update_project_version(self.TEST_PROJECT_DIRECTORY, "0.2.0-dev.1")

        logger.debug("Testing 'stable' reference version update for v0/old config format")
        self.assertEqual(
            configparser_v0.get_project_version(self.TEST_PROJECT_DIRECTORY, "stable"),
            "0.2.0"
        )

        logger.debug("Testing 'dev' reference version update for v0/old config format")
        self.assertEqual(
            configparser_v0.get_project_version(self.TEST_PROJECT_DIRECTORY, "dev"),
            "0.2.0-dev.1"
        )

        logger.debug("Testing 'dev' reference version update for v1/new config format")
        self.assertEqual(
            configparser_v1.get_project_version(self.TEST_PROJECT_DIRECTORY),
            "0.2.0-dev.1"
        )

        logger.debug("Testing file update call")
        mock_update.assert_called_with(configparser_v0.config_path, 'w')
        mock_update.assert_called_with(configparser_v1.config_path, 'w')

    @patch('builtins.open', new_callable=mock_open)
    def test_update_project_history(
            self,
            mock_update
    ):
        logger.info("Executing unit tests for 'ConfigParser.update_project_history' method")

        configparser_v0 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0

        configparser_v1 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1

        configparser_v1.update_project_history(
            self.TEST_PROJECT_DIRECTORY,
            bump_type="major",
            commit_sha="#######"
        )

        logger.debug("Testing 'history' parameter update for v0/old config format")
        self.assertEqual(
            configparser_v1.get_project_history(self.TEST_PROJECT_DIRECTORY),
            {
                "latest_bump_type": "major",
                "latest_bump_commit_hash": "#######"
            }
        )

        logger.debug("Testing file update call")
        mock_update.assert_called_with(configparser_v0.config_path, 'w')
        mock_update.assert_called_with(configparser_v1.config_path, 'w')

    @patch('src.comet.config.os')
    @patch('builtins.open', new_callable=mock_open, read_data=str(TestBaseConfig.TEST_GITFLOW_CONFIG_V1))
    def test_read_config(
            self,
            mock_read,
            mock_os
    ):
        logger.info("Executing unit tests for 'ConfigParser.read_config' method")

        logger.debug("Testing configuration file read without sanitization for v1/new config format")
        configparser_v1 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.read_config(sanitize=False)

        logger.debug("Testing file read call for v1/new config format")
        mock_read.assert_called_with(configparser_v1.config_path)

        logger.debug("Testing read data from the file for v1/new config format")
        self.assertEqual(
            configparser_v1.config,
            self.TEST_GITFLOW_CONFIG_V1
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

        configparser_v0 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v0.config = self.TEST_GITFLOW_CONFIG_V0
        configparser_v0.write_config()

        configparser_v1 = ConfigParser(
            config_path=self.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = self.TEST_GITFLOW_CONFIG_V1
        configparser_v1.write_config()

        logger.debug("Testing file update call for v0/old config format")
        mock_update.assert_called_with(configparser_v0.config_path, 'w')

        logger.debug("Testing file update call for v1/new config format")
        mock_update.assert_called_with(configparser_v1.config_path, 'w')

        logger.debug("Testing file update exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path="test_read_file"
            )
            configparser.config = self.TEST_GITFLOW_CONFIG_V1
            mock_update.side_effect = Exception()
            configparser.write_config()


if __name__ == '__main__':
    unittest.main()