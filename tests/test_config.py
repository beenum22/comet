import unittest
from unittest import TestCase
from unittest.mock import patch, mock_open
import logging
import copy

from .common import TestBaseConfig
from src.comet.config import ConfigParser

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class TestConfigParser(TestCase):

    def test_get_projects(self):
        logger.info("Executing unit tests for 'ConfigParser.get_projects' method")

        configparser_v1 = ConfigParser(
            config_path=f"test_comet.yml"
        )

        configparser_v1.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        logger.debug("Testing 'projects' fetch for v1/new config format")
        self.assertEqual(
            configparser_v1.get_projects(),
            [TestBaseConfig.TEST_REPO_DIRECTORY]
        )

        logger.debug("Testing projects fetch exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path=f"test_comet.yml"
            )
            configparser.get_projects()

    def test_get_project_history(self):
        logger.info("Executing unit tests for 'ConfigParser.get_project_history' method")

        configparser_v1 = ConfigParser(
            config_path=f"test_comet.yml"
        )
        configparser_v1.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        logger.debug("Testing 'history' get for v1/new config format")
        self.assertEqual(
            configparser_v1.get_project_history(
                configparser_v1.config["projects"][0]["path"]
            ),
            TestBaseConfig.TEST_PROJECT_HISTORY
        )

    def test_get_project_version(self):
        logger.info("Executing unit tests for 'ConfigParser.get_project_version' method")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        logger.debug("Testing version read for v1/new config format")
        self.assertEqual(
            configparser_v1.get_project_version(TestBaseConfig.TEST_REPO_DIRECTORY),
            TestBaseConfig.TEST_DEV_VERSION
        )

    def test_get_development_model_type(self):
        logger.info("Executing unit tests for 'ConfigParser.get_development_model_type' method")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        logger.debug("Testing development model fetch")
        self.assertEqual(
            configparser_v1.get_development_model_type(),
            TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]["strategy"]["development_model"]["type"]
        )

    def test_get_development_model_options(self):
        logger.info("Executing unit tests for 'ConfigParser.get_development_model_options' method")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        logger.debug("Testing development model fetch")
        self.assertEqual(
            configparser_v1.get_development_model_options(),
            TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]["strategy"]["development_model"]["options"]
        )

    def test_validate_config(self):
        logger.info("Executing unit tests for 'ConfigParser.validate_config' method")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        logger.debug("Testing development model fetch")
        self.assertIsNone(configparser_v1.validate_config())

    def test_update_project_version(
            self
    ):
        logger.info("Executing unit tests for 'ConfigParser.update_project_version' method")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = copy.deepcopy(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"])

        configparser_v1.update_project_version(TestBaseConfig.TEST_REPO_DIRECTORY, "0.2.0-dev.1")

        logger.debug("Testing 'dev' reference version update for v1/new config format")
        self.assertEqual(
            configparser_v1.get_project_version(TestBaseConfig.TEST_REPO_DIRECTORY),
            "0.2.0-dev.1"
        )

    def test_update_project_history(
            self
    ):
        logger.info("Executing unit tests for 'ConfigParser.update_project_history' method")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = copy.deepcopy(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"])

        configparser_v1.update_project_history(
            TestBaseConfig.TEST_REPO_DIRECTORY,
            bump_type="major",
            commit_sha="#######"
        )

        logger.debug("Testing 'history' parameter update")
        self.assertEqual(
            configparser_v1.get_project_history(TestBaseConfig.TEST_REPO_DIRECTORY),
            {
                "next_release_type": "major",
                "latest_bump_commit_hash": "#######"
            }
        )

    @patch('src.comet.config.os')
    @patch('builtins.open', new_callable=mock_open, read_data=str(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]))
    def test_read_config(
            self,
            mock_read,
            mock_os
    ):
        logger.info("Executing unit tests for 'ConfigParser.read_config' method")

        logger.debug("Testing configuration file read without sanitization")
        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.read_config(sanitize=False)

        logger.debug("Testing file read call")
        mock_read.assert_called_with(configparser_v1.config_path)

        logger.debug("Testing read data from the file")
        self.assertEqual(
            configparser_v1.config,
            TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        )

        logger.debug("Testing configuration file read without state and sanitization")
        configparser_v1_ohne_state = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE,
            skip_state=True
        )
        configparser_v1_ohne_state.read_config(sanitize=False)

        logger.debug("Testing read data from the file without project state")
        with self.assertRaises(KeyError):
            print(configparser_v1_ohne_state.config["projects"][0]["version"])
        with self.assertRaises(KeyError):
            print(configparser_v1_ohne_state.config["projects"][0]["history"])

        logger.debug("Testing incorrect configuration file path exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path="test_read_file"
            )
            mock_read.side_effect = Exception()
            configparser.read_config(sanitize=False)

    # TODO: Check if autospec is needed
    @patch('src.comet.config.yaml.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_config(
            self,
            mock_update,
            mock_yaml
    ):
        logger.info("Executing unit tests for 'ConfigParser.write_config' method")

        logger.debug("Testing configuration file read without sanitization")

        configparser_v1 = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE
        )
        configparser_v1.config = copy.deepcopy(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"])
        configparser_v1.write_config()

        logger.debug("Testing file update call")
        mock_update.assert_called_with(configparser_v1.config_path, 'w')
        mock_yaml.assert_called_with(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"], mock_update.return_value, sort_keys=False)

        logger.debug("Testing configuration file write without state")
        configparser_v1_ohne_state = ConfigParser(
            config_path=TestBaseConfig.TEST_GITFLOW_CONFIG_FILE,
            skip_state=True
        )
        configparser_v1_ohne_state.config = copy.deepcopy(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"])

        configparser_v1_ohne_state.write_config()

        logger.debug("Testing read data from the file without project state")
        mock_update.assert_called_with(configparser_v1.config_path, 'w')
        mock_yaml.assert_called_with(configparser_v1_ohne_state.config, mock_update.return_value, sort_keys=False)

        logger.debug("Testing file update exception handling")
        with self.assertRaises(Exception):
            configparser = ConfigParser(
                config_path="test_read_file"
            )
            configparser.config = copy.deepcopy(TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"])
            mock_update.side_effect = Exception()
            configparser.write_config()


if __name__ == '__main__':
    unittest.main()
