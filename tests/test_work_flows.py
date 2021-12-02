import unittest
from unittest.mock import patch
import logging

from .common import TestBaseConfig
from src.comet.work_flows import GitFlow

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class GitFlowTest(unittest.TestCase, TestBaseConfig):

    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    def test_prepare_workflow(self, mock_scm, mock_configparser):
        logger.info("Executing unit tests for 'GitFlow.prepare_workflow' method")

        flow = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        mock_configparser.assert_called_once_with(
            config_path=f"{self.TEST_PROJECT_DIRECTORY_1}/{self.TEST_GITFLOW_CONFIG_FILE}"
        )

        mock_scm.assert_called_once_with(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            repo=flow.project_config.config["repo"],
            workspace=flow.project_config.config["workspace"],
            repo_local_path=self.TEST_PROJECT_DIRECTORY_1,
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"]
        )

        # for scm in self.TEST_GIT_CONFIG["scm_providers"]:
        #     for connection_type in self.TEST_GIT_CONFIG["connection_types"]:
        #         flow = GitFlow(
        #             connection_type=connection_type,
        #             scm_provider=scm,
        #             username=self.TEST_GIT_CONFIG["username"],
        #             password=self.TEST_GIT_CONFIG["password"],
        #             ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
        #             project_local_path=self.TEST_PROJECT_DIRECTORY_1,
        #             project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
        #             push_changes=False
        #         )
        #
        #         mock_configparser.assert_called_with(
        #             config_path=f"{self.TEST_PROJECT_DIRECTORY_1}/{self.TEST_GITFLOW_CONFIG_FILE}"
        #         )
        #
        #         mock_scm.assert_called_with(
        #             scm_provider=scm,
        #             connection_type=connection_type,
        #             username=self.TEST_GIT_CONFIG["username"],
        #             password=self.TEST_GIT_CONFIG["password"],
        #             repo=flow.project_config.config["repo"],
        #             workspace=flow.project_config.config["workspace"],
        #             repo_local_path=self.TEST_PROJECT_DIRECTORY_1,
        #             ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"]
        #         )
        #
        # self.assertEqual(
        #     mock_configparser().read_config.call_count,
        #     len(self.TEST_GIT_CONFIG["connection_types"]) + len(self.TEST_GIT_CONFIG["scm_providers"])
        # )

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

        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v0"]

        gitflow_v0 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        gitflow_v0.prepare_versioning(reference_version_type="dev")

        for project in self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"]:
            mock_semver.assert_called_once_with(
                project_path=project["path"],
                version_files=project["version_files"],
                version_regex=project["version_regex"],
                project_version_file=f"{self.TEST_PROJECT_DIRECTORY_1}/{self.TEST_GITFLOW_CONFIG_FILE}",
                reference_version_type="dev"
            )

        mock_scm.reset_mock()
        mock_semver.reset_mock()
        mock_configparser.reset_mock()

        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        gitflow_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        gitflow_v1.prepare_versioning(reference_version_type=None)

        for project in self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"]:
            mock_semver.assert_called_once_with(
                project_path=project["path"],
                version_files=project["version_files"],
                version_regex=project["version_regex"],
                project_version_file=f"{self.TEST_PROJECT_DIRECTORY_1}/{self.TEST_GITFLOW_CONFIG_FILE}",
                reference_version_type=None
            )

    @patch.object(GitFlow, 'release_candidate')
    @patch.object(GitFlow, 'release_to_stable')
    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    @patch("src.comet.work_flows.SemVer")
    def test_release_flow(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_stable_release,
            mock_release_candidate
    ):
        logger.info("Executing unit tests for 'GitFlow.release_flow' method")

        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable release flow for mono repo with v1/new config format")
        gitflow_mono_v1.release_flow(branches=False)
        mock_stable_release.assert_called_once_with(gitflow_mono_v1.source_branch)
        mock_release_candidate.assert_not_called()

        mock_stable_release.reset_mock()
        mock_release_candidate.reset_mock()

        logger.debug("Testing release candidate flow for mono repo with v1/new config format")
        gitflow_mono_v1.release_flow(branches=True)
        mock_release_candidate.assert_called_once()
        mock_stable_release.assert_not_called()

        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()
        mock_stable_release.reset_mock()
        mock_release_candidate.reset_mock()
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]

        gitflow_multi_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_multi_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release candidate flow for multi repo with v1/new config format")
        with self.assertRaises(AssertionError):
            gitflow_multi_v1.release_flow(branches=True)

    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    @patch("src.comet.work_flows.SemVer")
    def test_sync_flow(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.sync_flow' method")

        logger.debug("Initializing GitFlow object with 'push_changes' set for mono repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        gitflow_mono_v1_with_push = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=True
        )
        gitflow_mono_v1_with_push.prepare_versioning(reference_version_type=None)

        logger.debug("Testing sync flow for mono repo with v1/new config format")
        gitflow_mono_v1_with_push.sync_flow()
        mock_scm().merge_branches.assert_called_once_with(
            source_branch=gitflow_mono_v1_with_push.stable_branch,
            destination_branch=gitflow_mono_v1_with_push.development_branch
        )
        mock_scm().push_changes.assert_called_once_with(
            branch=gitflow_mono_v1_with_push.development_branch,
            tags=False
        )

        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object without 'push_changes' set for mono repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        gitflow_mono_v1_with_push = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1_with_push.prepare_versioning(reference_version_type=None)

        logger.debug("Testing sync flow for mono repo with v1/new config format")
        gitflow_mono_v1_with_push.sync_flow()
        mock_scm().merge_branches.assert_called_once_with(
            source_branch=gitflow_mono_v1_with_push.stable_branch,
            destination_branch=gitflow_mono_v1_with_push.development_branch
        )
        mock_scm().push_changes.assert_not_called()

    @patch.object(GitFlow, 'development_branch_flow')
    @patch.object(GitFlow, 'stable_branch_flow')
    @patch.object(GitFlow, 'release_branch_flow')
    @patch.object(GitFlow, 'default_branch_flow')
    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    @patch("src.comet.work_flows.SemVer")
    def test_branch_flows(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_default_branch_flow,
            mock_release_branch_flow,
            mock_stable_branch_flow,
            mock_development_branch_flow
    ):
        logger.info("Executing unit tests for 'GitFlow.branch_flows' method")

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to development branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"]
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing development branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_development_branch_flow.assert_called_once()
        mock_release_branch_flow.assert_not_called()
        mock_stable_branch_flow.assert_not_called()
        mock_default_branch_flow.assert_not_called()

        mock_development_branch_flow.reset_mock()
        mock_release_branch_flow.reset_mock()
        mock_stable_branch_flow.reset_mock()
        mock_default_branch_flow.reset_mock()
        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to stable branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"]
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_stable_branch_flow.assert_called_once()
        mock_release_branch_flow.assert_not_called()
        mock_development_branch_flow.assert_not_called()
        mock_default_branch_flow.assert_not_called()

        mock_development_branch_flow.reset_mock()
        mock_release_branch_flow.reset_mock()
        mock_stable_branch_flow.reset_mock()
        mock_default_branch_flow.reset_mock()
        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to release branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = \
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["release_branch_prefix"]}/test'
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_release_branch_flow.assert_called_once()
        mock_stable_branch_flow.assert_not_called()
        mock_development_branch_flow.assert_not_called()
        mock_default_branch_flow.assert_not_called()

        mock_development_branch_flow.reset_mock()
        mock_release_branch_flow.reset_mock()
        mock_stable_branch_flow.reset_mock()
        mock_default_branch_flow.reset_mock()
        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to any feature/bugfix branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = "feature/test"
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing default branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_default_branch_flow.assert_called_once()
        mock_release_branch_flow.assert_not_called()
        mock_stable_branch_flow.assert_not_called()
        mock_development_branch_flow.assert_not_called()

    @patch.object(GitFlow, 'default_branch_flow')
    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    @patch("src.comet.work_flows.SemVer")
    def test_release_to_stable(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_default_branch_flow
    ):
        logger.info("Executing unit tests for 'GitFlow.release_to_stable' method")

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to development branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"]
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing development branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_development_branch_flow.assert_called_once()
        mock_release_branch_flow.assert_not_called()
        mock_stable_branch_flow.assert_not_called()
        mock_default_branch_flow.assert_not_called()

        mock_development_branch_flow.reset_mock()
        mock_release_branch_flow.reset_mock()
        mock_stable_branch_flow.reset_mock()
        mock_default_branch_flow.reset_mock()
        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to stable branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"]
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_stable_branch_flow.assert_called_once()
        mock_release_branch_flow.assert_not_called()
        mock_development_branch_flow.assert_not_called()
        mock_default_branch_flow.assert_not_called()

        mock_development_branch_flow.reset_mock()
        mock_release_branch_flow.reset_mock()
        mock_stable_branch_flow.reset_mock()
        mock_default_branch_flow.reset_mock()
        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to release branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = \
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["release_branch_prefix"]}/test'
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_release_branch_flow.assert_called_once()
        mock_stable_branch_flow.assert_not_called()
        mock_development_branch_flow.assert_not_called()
        mock_default_branch_flow.assert_not_called()

        mock_development_branch_flow.reset_mock()
        mock_release_branch_flow.reset_mock()
        mock_stable_branch_flow.reset_mock()
        mock_default_branch_flow.reset_mock()
        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
                     "set to any feature/bugfix branch")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_scm().get_active_branch.return_value = "feature/test"
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_PROJECT_DIRECTORY_1,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing default branch flow for mono repo with v1/new config format")
        gitflow_mono_v1.branch_flows()
        mock_default_branch_flow.assert_called_once()
        mock_release_branch_flow.assert_not_called()
        mock_stable_branch_flow.assert_not_called()
        mock_development_branch_flow.assert_not_called()


if __name__ == '__main__':
    unittest.main()