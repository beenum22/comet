import unittest
from unittest.mock import patch
import logging

from src.comet.work_flows import GitFlow

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class GitFlowTest(unittest.TestCase):

    TEST_DEV_VERSION = "0.1.0-dev.1"
    TEST_STABLE_VERSION = "0.1.0"
    TEST_DIRECTORY = "test_project"
    TEST_PROJECT_CONFIG_FILE = "test_project/.comet.yml"
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
                "path": ".",
                "stable_version": TEST_STABLE_VERSION,
                "dev_version": TEST_DEV_VERSION,
                "version_regex": "",
                "version_files": [
                    TEST_PROJECT_VERSION_FILE
                ]
            }
        ]
    }

    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    def test_prepare_workflow(self, mock_scm, mock_configparser):
        logger.info("Executing unit tests for 'GitFlow.prepare_workflow' method")

        GitFlow(
            connection_type="https",
            scm_provider="bitbucket",
            username="dummy",
            password="test",
            ssh_private_key_path="~/.ssh/id_rsa",
            project_local_path="./",
            project_config_path=self.TEST_PROJECT_CONFIG_FILE,
            push_changes=False
        )

        mock_configparser.assert_called_once_with(config_path=self.TEST_PROJECT_CONFIG_FILE)
        mock_configparser().read_config.assert_called_once()

        mock_scm.assert_called_once()

    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    @patch("src.comet.work_flows.SemVer")
    def test_prepare_versioning(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.prepare_versioning' method")

        mock_configparser.return_value.config = self.TEST_PROJECT_CONFIG
        mock_semver.return_value.version_object = self.TEST_PROJECT_CONFIG

        gitflow = GitFlow(
            connection_type="https",
            scm_provider="bitbucket",
            username="dummy",
            password="test",
            ssh_private_key_path="~/.ssh/id_rsa",
            project_local_path="./",
            project_config_path=self.TEST_PROJECT_CONFIG_FILE,
            push_changes=False
        )
        gitflow.prepare_versioning(reference_version_type="dev")

        mock_semver.assert_called_once_with(
            project_path=".",
            version_files=[
                self.TEST_PROJECT_VERSION_FILE
            ],
            version_regex="",
            project_version_file=self.TEST_PROJECT_CONFIG_FILE,
            reference_version_type="dev"
        )


if __name__ == '__main__':
    unittest.main()