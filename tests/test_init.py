from unittest import TestCase
from unittest.mock import patch
import logging
import copy

from .common import TestBaseConfig
# from src.comet.init import InitRepo, State, ConfigParser
from src.comet.init import InitRepo, State, ConfigParser, Scm, ConventionalCommits

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class TestState(TestCase):

    @patch("src.comet.init.ConfigParser", autospec=True)
    @patch("src.comet.init.Scm", autospec=True)
    def test_has_state(self, mock_scm, mock_configparser):
        logger.info("Executing unit tests for 'State.has_state' method")

        configparser = ConfigParser(
            config_path=f"test_comet.yml"
        )



        mock_scm().has_local_reference.return_value = False
        project_state = State(
            mock_configparser,
            mock_scm
        )

        logger.debug("Testing when state reference doesn't exist")
        self.assertFalse(project_state.has_state("test"))

        # mock_scm.reset_mock()

        # logger.debug("Testing when state reference exist")
        # mock_scm().has_local_reference.return_value = True
        # self.assertTrue(project_state.has_state("test"))

    def test_get_state(self):
        self.fail()

    def test_create_state(self):
        self.fail()

    def test_update_state(self):
        self.fail()

    def test_prepare_config(self):
        self.fail()


class TestInitRepo(TestCase, TestBaseConfig):

    @patch("src.comet.init.State", autospec=True)
    @patch("src.comet.init.Scm", autospec=True)
    @patch("src.comet.init.ConfigParser.write_config", autospec=True)
    @patch("src.comet.init.ConfigParser.has_config_file", autospec=True)
    def test_initialize_config(
            self,
            mock_has_config,
            mock_write_config,
            mock_scm,
            mock_state
    ):
        logger.info("Executing unit tests for 'InitRepo.initialize_config' method")

        logger.debug("Testing configuration initialization without Git notes state")
        with patch("builtins.input", side_effect=["beenum22", "comet", "gitflow", "main", "develop", "release", "conventional_commits", "no"]) as init:
            init_config = InitRepo(
                repo_config_path=self.TEST_GITFLOW_CONFIG_FILE,
                repo_local_path=self.TEST_REPO_DIRECTORY,
                git_notes_state_backend=False
            )

            logger.debug("Testing configuration initialization when no config file is found")
            mock_has_config.return_value = False

            init_config.initialize_config()
            mock_write_config.assert_called_once()
            mock_scm.return_value.commit_changes.assert_called_once_with(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                init_config.repo_config_path,
                init_config.push_changes
            )
            self.assertEqual(init_config.config_object.config, self.TEST_GITFLOW_CONFIGS["mono"]["init"])

            logger.debug("Testing configuration initialization exception when config file is already initialized")
            mock_has_config.return_value = True
            with self.assertRaises(Exception):
                init_config.initialize_config()

        mock_write_config.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Testing configuration initialization with Git notes state")
        with patch("builtins.input", side_effect=["beenum22", "comet", "gitflow", "main", "develop", "release", "conventional_commits", "no"]) as init:
            init_config_with_state = InitRepo(
                repo_config_path=self.TEST_GITFLOW_CONFIG_FILE,
                repo_local_path=self.TEST_REPO_DIRECTORY,
                git_notes_state_backend=True
            )

            logger.debug("Testing configuration initialization when state ref is found")
            mock_has_config.return_value = False
            mock_scm().has_local_reference.return_value = True

            init_config_with_state.initialize_config()
            mock_state.assert_called_once()
            mock_state.return_value.get_state.assert_called_once()
            mock_state.return_value.create_state.assert_called_once()
            mock_write_config.assert_called_once()
            mock_scm.return_value.commit_changes.assert_called_once_with(
                ConventionalCommits.DEFAULT_VERSION_COMMIT,
                init_config_with_state.repo_config_path,
                init_config_with_state.push_changes
            )
            self.assertEqual(init_config_with_state.config_object.config, self.TEST_GITFLOW_CONFIGS["mono"]["init"])
