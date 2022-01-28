import unittest
from unittest.mock import patch, call
import logging
from random import sample, randint
import os

from .common import TestBaseConfig, TestBaseCommitMessages
from src.comet.work_flows import GitFlow
from src.comet.conventions import ConventionalCommits
from src.comet.scm import Scm

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class GitFlowTestV0(unittest.TestCase, TestBaseConfig, TestBaseCommitMessages):

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
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        mock_configparser.assert_called_once_with(
            config_path=f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}"
        )

        mock_scm.assert_called_once_with(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            repo=flow.project_config.config["repo"],
            workspace=flow.project_config.config["workspace"],
            repo_local_path=self.TEST_REPO_DIRECTORY,
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"]
        )

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
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        gitflow_v0.prepare_versioning(reference_version_type="dev")

        for project in self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"]:
            mock_semver.assert_called_once_with(
                project_path=project["path"],
                version_files=project["version_files"],
                version_regex=project["version_regex"],
                project_version_file=f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}",
                reference_version_type="dev"
            )

    # TODO: Configure for v0 config
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_multi_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release candidate flow for multi repo with v1/new config format")
        with self.assertRaises(AssertionError):
            gitflow_multi_v1.release_flow(branches=True)

    # TODO: configure for v0 config
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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

    # TODO: Configure v0 config
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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

    @staticmethod
    def side_effect_find_new_commits(source_branch: str, destination_branch: str, project_path: str) -> list:
        project_commits = sample(
            TestBaseCommitMessages.TEST_DUMMY_COMMITS, randint(1, len(TestBaseCommitMessages.TEST_DUMMY_COMMITS))
        )
        return project_commits

    # TODO: use Mock `auto_spec` flag
    @patch("src.comet.work_flows.ConfigParser")
    @patch("src.comet.work_flows.Scm")
    @patch("src.comet.work_flows.SemVer")
    def test_release_project_version(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.release_project_version' method")

        logger.debug("Initializing GitFlow object for mono repo with v0/old config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.has_deprecated_config_parameter.return_value = True
        mock_scm().find_new_commits.side_effect = GitFlowTest.side_effect_find_new_commits
        mock_semver().get_version.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"]
        mock_semver().get_final_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]

        gitflow_mono_v0 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v0.prepare_versioning(reference_version_type="dev")

        logger.debug("Testing release/finalization of a project version for mono repo with v0/old "
                     "config format")
        self.assertTrue(
            gitflow_mono_v0.release_project_version(
                self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"],
                self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["development_branch"]
            )
        )
        mock_semver().get_version.assert_called_once()
        mock_semver().get_final_version.assert_called_once()
        mock_scm().find_new_commits.assert_called_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["development_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["stable_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"]
        )
        mock_semver().update_version_files.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]
        )
        mock_configparser().update_project_version.assert_has_calls(
            [
                call(
                    self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"],
                    self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0],
                    version_type="stable"
                ),
                call(
                    self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"],
                    self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0],
                    version_type="dev"
                )
            ]
        )

        logger.debug("Resetting Mocks")
        mock_semver.reset_mock()
        mock_configparser.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.has_deprecated_config_parameter.return_value = False
        mock_scm().find_new_commits.side_effect = GitFlowTest.side_effect_find_new_commits
        mock_semver().get_version.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"]
        mock_semver().get_final_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release/finalization of a project version for mono repo with v1/new "
                     "config format")
        self.assertTrue(
            gitflow_mono_v1.release_project_version(
                self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
                self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"]
            )
        )
        mock_semver().get_version.assert_called_once()
        mock_semver().get_final_version.assert_called_once()
        mock_scm().find_new_commits.assert_called_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
        )
        mock_semver().update_version_files.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        )
        mock_configparser().update_project_version.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0],
            version_type=None
        )

    # @patch.object(GitFlow, 'release_project_version')
    # @patch("src.comet.work_flows.ConfigParser")
    # @patch("src.comet.work_flows.Scm")
    # @patch("src.comet.work_flows.SemVer")
    # def test_release_to_stable(
    #         self,
    #         mock_semver,
    #         mock_scm,
    #         mock_configparser,
    #         mock_release_project
    # ):
    #     logger.info("Executing unit tests for 'GitFlow.release_to_stable' method")
    #
    #     logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
    #     mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]
    #     mock_semver().get_version.return_value = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"][0]["version"]
    #     mock_semver().get_final_version.return_value = \
    #         self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"][0]["version"].split("-")[0]
    #     mock_release_project.return_value = True
    #     gitflow_mono_v1 = GitFlow(
    #         scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #         connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #         username=self.TEST_GIT_CONFIG["username"],
    #         password=self.TEST_GIT_CONFIG["password"],
    #         ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #         project_local_path=self.TEST_REPO_DIRECTORY,
    #         project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #         push_changes=True
    #     )
    #     gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #
    #     logger.debug("Testing stable release flow from development branch for multi repo with v1/new "
    #                  "config format")
    #     release_projects = \
    #         gitflow_mono_v1.release_to_stable(self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"])
    #
    #     self.assertCountEqual(
    #         release_projects,
    #         [project_dict["path"] for project_dict in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
    #     )
    #     print(mock_semver().get_version.call_count)
    #     self.assertEqual(
    #         mock_semver().get_version.call_count,
    #         len(self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"])
    #     )
    #     self.assertEqual(
    #         mock_semver().get_final_version.call_count,
    #         len(self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"])
    #     )
    #     mock_scm().add_tag.assert_has_calls(
    #         [
    #             call(
    #                 f'{self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["projects"][0]}{"-" if project_name else ""}{release_version}'
    #             ),
    #             call(
    #                 self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"],
    #                 self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0],
    #                 version_type="dev"
    #             )
    #         ]
    #     )
    #
    #
    #     logger.debug("Testing stable release flow from an invalid branch for multi repo with v1/new "
    #                  "config format")
    #     with self.assertRaises(AssertionError):
    #         gitflow_mono_v1.release_to_stable("feature/test")
    #
    #     # mock_development_branch_flow.assert_called_once()
    #     # mock_release_branch_flow.assert_not_called()
    #     # mock_stable_branch_flow.assert_not_called()
    #     # mock_default_branch_flow.assert_not_called()
    #     #
    #     # mock_development_branch_flow.reset_mock()
    #     # mock_release_branch_flow.reset_mock()
    #     # mock_stable_branch_flow.reset_mock()
    #     # mock_default_branch_flow.reset_mock()
    #     # mock_configparser.reset_mock()
    #     # mock_semver.reset_mock()
    #     # mock_scm.reset_mock()
    #     #
    #     # logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
    #     #              "set to stable branch")
    #     # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
    #     # mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"]
    #     # gitflow_mono_v1 = GitFlow(
    #     #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #     #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #     #     username=self.TEST_GIT_CONFIG["username"],
    #     #     password=self.TEST_GIT_CONFIG["password"],
    #     #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #     #     project_local_path=self.TEST_REPO_DIRECTORY,
    #     #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #     #     push_changes=False
    #     # )
    #     # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #     #
    #     # logger.debug("Testing stable branch flow for mono repo with v1/new config format")
    #     # gitflow_mono_v1.branch_flows()
    #     # mock_stable_branch_flow.assert_called_once()
    #     # mock_release_branch_flow.assert_not_called()
    #     # mock_development_branch_flow.assert_not_called()
    #     # mock_default_branch_flow.assert_not_called()
    #     #
    #     # mock_development_branch_flow.reset_mock()
    #     # mock_release_branch_flow.reset_mock()
    #     # mock_stable_branch_flow.reset_mock()
    #     # mock_default_branch_flow.reset_mock()
    #     # mock_configparser.reset_mock()
    #     # mock_semver.reset_mock()
    #     # mock_scm.reset_mock()
    #     #
    #     # logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
    #     #              "set to release branch")
    #     # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
    #     # mock_scm().get_active_branch.return_value = \
    #     #     f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["release_branch_prefix"]}/test'
    #     # gitflow_mono_v1 = GitFlow(
    #     #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #     #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #     #     username=self.TEST_GIT_CONFIG["username"],
    #     #     password=self.TEST_GIT_CONFIG["password"],
    #     #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #     #     project_local_path=self.TEST_REPO_DIRECTORY,
    #     #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #     #     push_changes=False
    #     # )
    #     # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #     #
    #     # logger.debug("Testing release branch flow for mono repo with v1/new config format")
    #     # gitflow_mono_v1.branch_flows()
    #     # mock_release_branch_flow.assert_called_once()
    #     # mock_stable_branch_flow.assert_not_called()
    #     # mock_development_branch_flow.assert_not_called()
    #     # mock_default_branch_flow.assert_not_called()
    #     #
    #     # mock_development_branch_flow.reset_mock()
    #     # mock_release_branch_flow.reset_mock()
    #     # mock_stable_branch_flow.reset_mock()
    #     # mock_default_branch_flow.reset_mock()
    #     # mock_configparser.reset_mock()
    #     # mock_semver.reset_mock()
    #     # mock_scm.reset_mock()
    #     #
    #     # logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
    #     #              "set to any feature/bugfix branch")
    #     # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
    #     # mock_scm().get_active_branch.return_value = "feature/test"
    #     # gitflow_mono_v1 = GitFlow(
    #     #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #     #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #     #     username=self.TEST_GIT_CONFIG["username"],
    #     #     password=self.TEST_GIT_CONFIG["password"],
    #     #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #     #     project_local_path=self.TEST_REPO_DIRECTORY,
    #     #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #     #     push_changes=False
    #     # )
    #     # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #     #
    #     # logger.debug("Testing default branch flow for mono repo with v1/new config format")
    #     # gitflow_mono_v1.branch_flows()
    #     # mock_default_branch_flow.assert_called_once()
    #     # mock_release_branch_flow.assert_not_called()
    #     # mock_stable_branch_flow.assert_not_called()
    #     # mock_development_branch_flow.assert_not_called()

    @patch.object(GitFlow, 'release_project_version')
    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_release_to_stable(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_release_project
    ):
        logger.info("Executing unit tests for 'GitFlow.release_to_stable' method")

        logger.debug("Initializing GitFlow object for multi repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]
        mock_semver().get_final_version.side_effect = [
            project["version"].split("-")[0] for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]
        ]
        mock_release_project.return_value = True
        gitflow_multi_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=True
        )
        gitflow_multi_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable release flow from development branch for multi repo with v1/new "
                     "config format")
        release_projects = \
            gitflow_multi_v1.release_to_stable(self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"])

        self.assertCountEqual(
            release_projects,
            [project_dict["path"] for project_dict in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
        )
        release_project_calls = [call(
            project["path"],
            self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"]
        ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
        mock_release_project.assert_has_calls(release_project_calls)
        tag_calls = [
            call(
                f'{os.path.basename(project["path"]).strip(".")}'
                f'{"-" if os.path.basename(project["path"]).strip(".") else ""}{project["version"].split("-")[0]}'
            ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]
        ]
        mock_scm().commit_changes.assert_called_once_with(
            ConventionalCommits.DEFAULT_VERSION_COMMIT,
            f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}",
            *release_projects,
            push=True
        )
        mock_scm().merge_branches.assert_called_once_with(
            source_branch=self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"],
            destination_branch=self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["stable_branch"]
        )
        mock_scm().add_tag.assert_has_calls(tag_calls)
        mock_scm().push_changes.assert_called_once_with(
            branch=self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["stable_branch"],
            tags=True
        )

        logger.debug("Testing stable release flow from an invalid branch for multi repo with v1/new "
                     "config format")
        with self.assertRaises(AssertionError):
            gitflow_multi_v1.release_to_stable("feature/test")

        mock_configparser.reset_mock()
        mock_semver.reset_mock()
        mock_scm.reset_mock()

        logger.debug("Initializing GitFlow object for multi repo with v0/old config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v0"]
        mock_semver().get_final_version.side_effect = [
            project["dev_version"].split("-")[0] for project in self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["projects"]
        ]
        mock_release_project.return_value = True
        gitflow_multi_v0 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=True
        )
        gitflow_multi_v0.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable release flow from development branch for multi repo with v0/old "
                     "config format")
        release_projects = \
            gitflow_multi_v0.release_to_stable(self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["development_branch"])

        self.assertCountEqual(
            release_projects,
            [project_dict["path"] for project_dict in self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["projects"]]
        )
        release_project_calls = [call(
            project["path"],
            self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["development_branch"]
        ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["projects"]]
        mock_release_project.assert_has_calls(release_project_calls)
        tag_calls = [
            call(
                f'{os.path.basename(project["path"]).strip(".")}'
                f'{"-" if os.path.basename(project["path"]).strip(".") else ""}{project["dev_version"].split("-")[0]}'
            ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["projects"]
        ]
        mock_scm().commit_changes.assert_called_once_with(
            ConventionalCommits.DEFAULT_VERSION_COMMIT,
            f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}",
            *release_projects,
            push=True
        )
        mock_scm().merge_branches.assert_called_once_with(
            source_branch=self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["development_branch"],
            destination_branch=self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["stable_branch"]
        )
        mock_scm().add_tag.assert_has_calls(tag_calls)
        mock_scm().push_changes.assert_called_once_with(
            branch=self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["stable_branch"],
            tags=True
        )

    @staticmethod
    def side_effect_release_branch(branch):
        if "release/" in branch:
            return False
        return True

    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_create_project_rc(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.create_project_rc' method")

        logger.debug("Initializing GitFlow object for mono repo with v0/old config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v0"]
        mock_configparser.return_value.has_deprecated_config_parameter.return_value = True
        # mock_scm().find_new_commits.side_effect = GitFlowTest.side_effect_find_new_commits
        mock_scm().has_local_branch.side_effect = GitFlowTest.side_effect_release_branch
        mock_scm().has_remote_branch.side_effect = GitFlowTest.side_effect_release_branch
        mock_configparser().get_project_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"]
        mock_semver().get_version.return_value = \
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]}-rc.1'
        mock_semver().get_final_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]

        gitflow_mono_v0 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v0.prepare_versioning(reference_version_type="dev")

        logger.debug("Testing release/finalization of a project version for mono repo with v0/old "
                     "config format")
        self.assertTrue(
            gitflow_mono_v0.create_project_rc(
                self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"]
            )
        )
        mock_semver().get_final_version.assert_called_once()
        mock_scm().has_local_branch.assert_called_with(
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["release_branch_prefix"]}/'
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]}'
        )
        mock_scm().add_branch.assert_called_once_with(
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["release_branch_prefix"]}/'
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]}',
            checkout=True
        )
        #
        mock_semver().update_version_files.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"],
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]}-rc.1'
        )
        mock_configparser().update_project_version.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"],
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0]}-rc.1',
            version_type="dev"
        )

        logger.debug("Resetting Mocks")
        mock_semver.reset_mock()
        mock_configparser.reset_mock()
        mock_scm.reset_mock()

        # logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
        # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        # mock_configparser.return_value.has_deprecated_config_parameter.return_value = False
        # mock_scm().find_new_commits.side_effect = GitFlowTest.side_effect_find_new_commits
        # mock_semver().get_version.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"]
        # mock_semver().get_final_version.return_value = \
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        # gitflow_mono_v1 = GitFlow(
        #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
        #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
        #     username=self.TEST_GIT_CONFIG["username"],
        #     password=self.TEST_GIT_CONFIG["password"],
        #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
        #     project_local_path=self.TEST_REPO_DIRECTORY,
        #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
        #     push_changes=False
        # )
        # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
        #
        # logger.debug("Testing release/finalization of a project version for mono repo with v1/new "
        #              "config format")
        # self.assertTrue(
        #     gitflow_mono_v1.release_project_version(
        #         self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
        #         self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"]
        #     )
        # )
        # mock_semver().get_version.assert_called_once()
        # mock_semver().get_final_version.assert_called_once()
        # mock_scm().find_new_commits.assert_called_with(
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"],
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"],
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
        # )
        # mock_semver().update_version_files.assert_called_once_with(
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"],
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        # )
        # mock_configparser().update_project_version.assert_called_once_with(
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
        #     self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0],
        #     version_type=None
        # )


class GitFlowTestV1(unittest.TestCase, TestBaseConfig, TestBaseCommitMessages):

    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    def test_prepare_workflow(self, mock_scm, mock_configparser):
        logger.info("Executing unit tests for 'GitFlow.prepare_workflow' method")

        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        flow = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        mock_configparser.assert_called_once_with(
            config_path=f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}"
        )

        mock_scm.assert_called_once_with(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            repo=flow.project_config.config["repo"],
            workspace=flow.project_config.config["workspace"],
            repo_local_path=self.TEST_REPO_DIRECTORY,
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
        #             project_local_path=self.TEST_REPO_DIRECTORY,
        #             project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
        #             push_changes=False
        #         )
        #
        #         mock_configparser.assert_called_with(
        #             config_path=f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}"
        #         )
        #
        #         mock_scm.assert_called_with(
        #             scm_provider=scm,
        #             connection_type=connection_type,
        #             username=self.TEST_GIT_CONFIG["username"],
        #             password=self.TEST_GIT_CONFIG["password"],
        #             repo=flow.project_config.config["repo"],
        #             workspace=flow.project_config.config["workspace"],
        #             repo_local_path=self.TEST_REPO_DIRECTORY,
        #             ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"]
        #         )
        #
        # self.assertEqual(
        #     mock_configparser().read_config.call_count,
        #     len(self.TEST_GIT_CONFIG["connection_types"]) + len(self.TEST_GIT_CONFIG["scm_providers"])
        # )

    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_prepare_versioning(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.prepare_versioning' method")

        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]

        gitflow_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )

        gitflow_v1.prepare_versioning(reference_version_type=None)

        for project in self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"]:
            mock_semver.assert_called_once_with(
                project_path=project["path"],
                version_files=project["version_files"],
                version_regex=project["version_regex"],
                project_version_file=f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}",
                reference_version_type=None
            )

    # TODO: Fix tests with autospec
    @patch.object(GitFlow, 'release_candidate', autospec=True)
    @patch.object(GitFlow, 'release_to_stable', autospec=True)
    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
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
        mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"]

        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_multi_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release candidate flow for multi repo with v1/new config format")
        with self.assertRaises(AssertionError):
            gitflow_multi_v1.release_flow(branches=True)

    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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

    @patch.object(GitFlow, 'development_branch_flow', autospec=True)
    @patch.object(GitFlow, 'stable_branch_flow', autospec=True)
    @patch.object(GitFlow, 'release_branch_flow', autospec=True)
    @patch.object(GitFlow, 'default_branch_flow', autospec=True)
    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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
            project_local_path=self.TEST_REPO_DIRECTORY,
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

    @staticmethod
    def side_effect_find_new_commits(source_branch: str, destination_branch: str, project_path: str) -> list:
        project_commits = sample(
            TestBaseCommitMessages.TEST_DUMMY_COMMITS.keys(),
            randint(1, len(TestBaseCommitMessages.TEST_DUMMY_COMMITS))
        )
        return project_commits

    @staticmethod
    def side_effect_get_commit_message(commit_hash) -> list:
        return TestBaseCommitMessages.TEST_DUMMY_COMMITS[commit_hash]

    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_release_project_version(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.release_project_version' method")

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.has_deprecated_config_parameter.return_value = False
        mock_scm().find_new_commits.side_effect = GitFlowTestV1.side_effect_find_new_commits
        mock_semver().get_version.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"]
        mock_semver().get_final_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release/finalization of a project version for mono repo with v1/new "
                     "config format")
        self.assertTrue(
            gitflow_mono_v1.release_project_version(
                self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
                self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"]
            )
        )
        mock_semver().get_version.assert_called_once()
        mock_semver().get_final_version.assert_called_once()
        mock_scm().find_new_commits.assert_called_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
        )
        mock_semver().update_version_files.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        )
        mock_configparser().update_project_version.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0],
            version_type=None
        )

    # @patch.object(GitFlow, 'release_project_version')
    # @patch("src.comet.work_flows.ConfigParser")
    # @patch("src.comet.work_flows.Scm")
    # @patch("src.comet.work_flows.SemVer")
    # def test_release_to_stable(
    #         self,
    #         mock_semver,
    #         mock_scm,
    #         mock_configparser,
    #         mock_release_project
    # ):
    #     logger.info("Executing unit tests for 'GitFlow.release_to_stable' method")
    #
    #     logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
    #     mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]
    #     mock_semver().get_version.return_value = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"][0]["version"]
    #     mock_semver().get_final_version.return_value = \
    #         self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"][0]["version"].split("-")[0]
    #     mock_release_project.return_value = True
    #     gitflow_mono_v1 = GitFlow(
    #         scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #         connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #         username=self.TEST_GIT_CONFIG["username"],
    #         password=self.TEST_GIT_CONFIG["password"],
    #         ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #         project_local_path=self.TEST_REPO_DIRECTORY,
    #         project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #         push_changes=True
    #     )
    #     gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #
    #     logger.debug("Testing stable release flow from development branch for multi repo with v1/new "
    #                  "config format")
    #     release_projects = \
    #         gitflow_mono_v1.release_to_stable(self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"])
    #
    #     self.assertCountEqual(
    #         release_projects,
    #         [project_dict["path"] for project_dict in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
    #     )
    #     print(mock_semver().get_version.call_count)
    #     self.assertEqual(
    #         mock_semver().get_version.call_count,
    #         len(self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"])
    #     )
    #     self.assertEqual(
    #         mock_semver().get_final_version.call_count,
    #         len(self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"])
    #     )
    #     mock_scm().add_tag.assert_has_calls(
    #         [
    #             call(
    #                 f'{self.TEST_GITFLOW_CONFIGS["multi"]["v0"]["projects"][0]}{"-" if project_name else ""}{release_version}'
    #             ),
    #             call(
    #                 self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["path"],
    #                 self.TEST_GITFLOW_CONFIGS["mono"]["v0"]["projects"][0]["dev_version"].split("-")[0],
    #                 version_type="dev"
    #             )
    #         ]
    #     )
    #
    #
    #     logger.debug("Testing stable release flow from an invalid branch for multi repo with v1/new "
    #                  "config format")
    #     with self.assertRaises(AssertionError):
    #         gitflow_mono_v1.release_to_stable("feature/test")
    #
    #     # mock_development_branch_flow.assert_called_once()
    #     # mock_release_branch_flow.assert_not_called()
    #     # mock_stable_branch_flow.assert_not_called()
    #     # mock_default_branch_flow.assert_not_called()
    #     #
    #     # mock_development_branch_flow.reset_mock()
    #     # mock_release_branch_flow.reset_mock()
    #     # mock_stable_branch_flow.reset_mock()
    #     # mock_default_branch_flow.reset_mock()
    #     # mock_configparser.reset_mock()
    #     # mock_semver.reset_mock()
    #     # mock_scm.reset_mock()
    #     #
    #     # logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
    #     #              "set to stable branch")
    #     # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
    #     # mock_scm().get_active_branch.return_value = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"]
    #     # gitflow_mono_v1 = GitFlow(
    #     #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #     #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #     #     username=self.TEST_GIT_CONFIG["username"],
    #     #     password=self.TEST_GIT_CONFIG["password"],
    #     #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #     #     project_local_path=self.TEST_REPO_DIRECTORY,
    #     #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #     #     push_changes=False
    #     # )
    #     # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #     #
    #     # logger.debug("Testing stable branch flow for mono repo with v1/new config format")
    #     # gitflow_mono_v1.branch_flows()
    #     # mock_stable_branch_flow.assert_called_once()
    #     # mock_release_branch_flow.assert_not_called()
    #     # mock_development_branch_flow.assert_not_called()
    #     # mock_default_branch_flow.assert_not_called()
    #     #
    #     # mock_development_branch_flow.reset_mock()
    #     # mock_release_branch_flow.reset_mock()
    #     # mock_stable_branch_flow.reset_mock()
    #     # mock_default_branch_flow.reset_mock()
    #     # mock_configparser.reset_mock()
    #     # mock_semver.reset_mock()
    #     # mock_scm.reset_mock()
    #     #
    #     # logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
    #     #              "set to release branch")
    #     # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
    #     # mock_scm().get_active_branch.return_value = \
    #     #     f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["release_branch_prefix"]}/test'
    #     # gitflow_mono_v1 = GitFlow(
    #     #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #     #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #     #     username=self.TEST_GIT_CONFIG["username"],
    #     #     password=self.TEST_GIT_CONFIG["password"],
    #     #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #     #     project_local_path=self.TEST_REPO_DIRECTORY,
    #     #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #     #     push_changes=False
    #     # )
    #     # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #     #
    #     # logger.debug("Testing release branch flow for mono repo with v1/new config format")
    #     # gitflow_mono_v1.branch_flows()
    #     # mock_release_branch_flow.assert_called_once()
    #     # mock_stable_branch_flow.assert_not_called()
    #     # mock_development_branch_flow.assert_not_called()
    #     # mock_default_branch_flow.assert_not_called()
    #     #
    #     # mock_development_branch_flow.reset_mock()
    #     # mock_release_branch_flow.reset_mock()
    #     # mock_stable_branch_flow.reset_mock()
    #     # mock_default_branch_flow.reset_mock()
    #     # mock_configparser.reset_mock()
    #     # mock_semver.reset_mock()
    #     # mock_scm.reset_mock()
    #     #
    #     # logger.debug("Initializing GitFlow object for mono repo with v1/new config format and source branch "
    #     #              "set to any feature/bugfix branch")
    #     # mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
    #     # mock_scm().get_active_branch.return_value = "feature/test"
    #     # gitflow_mono_v1 = GitFlow(
    #     #     scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
    #     #     connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
    #     #     username=self.TEST_GIT_CONFIG["username"],
    #     #     password=self.TEST_GIT_CONFIG["password"],
    #     #     ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
    #     #     project_local_path=self.TEST_REPO_DIRECTORY,
    #     #     project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
    #     #     push_changes=False
    #     # )
    #     # gitflow_mono_v1.prepare_versioning(reference_version_type=None)
    #     #
    #     # logger.debug("Testing default branch flow for mono repo with v1/new config format")
    #     # gitflow_mono_v1.branch_flows()
    #     # mock_default_branch_flow.assert_called_once()
    #     # mock_release_branch_flow.assert_not_called()
    #     # mock_stable_branch_flow.assert_not_called()
    #     # mock_development_branch_flow.assert_not_called()

    @patch.object(GitFlow, 'release_project_version')
    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_release_to_stable(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_release_project
    ):
        logger.info("Executing unit tests for 'GitFlow.release_to_stable' method")

        logger.debug("Initializing GitFlow object for multi repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]
        mock_semver().get_final_version.side_effect = [
            project["version"].split("-")[0] for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]
        ]
        mock_release_project.return_value = True
        gitflow_multi_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=True
        )
        gitflow_multi_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable release flow from development branch for multi repo with v1/new "
                     "config format")
        release_projects = \
            gitflow_multi_v1.release_to_stable(self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"])

        self.assertCountEqual(
            release_projects,
            [project_dict["path"] for project_dict in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
        )
        release_project_calls = [call(
            project["path"],
            self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"]
        ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
        mock_release_project.assert_has_calls(release_project_calls)
        tag_calls = [
            call(
                f'{os.path.basename(project["path"]).strip(".")}'
                f'{"-" if os.path.basename(project["path"]).strip(".") else ""}{project["version"].split("-")[0]}'
            ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]
        ]
        mock_scm().commit_changes.assert_called_once_with(
            ConventionalCommits.DEFAULT_VERSION_COMMIT,
            f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}",
            *release_projects,
            push=True
        )
        mock_scm().merge_branches.assert_called_once_with(
            source_branch=self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["development_branch"],
            destination_branch=self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["stable_branch"]
        )
        mock_scm().add_tag.assert_has_calls(tag_calls)
        mock_scm().push_changes.assert_called_once_with(
            branch=self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["stable_branch"],
            tags=True
        )

        logger.debug("Testing stable release flow from an invalid branch for multi repo with v1/new "
                     "config format")
        with self.assertRaises(AssertionError):
            gitflow_multi_v1.release_to_stable("feature/test")

    @staticmethod
    def side_effect_release_branch(branch):
        if "release/" in branch:
            return False
        return True

    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_create_project_rc(
            self,
            mock_semver,
            mock_scm,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'GitFlow.create_project_rc' method")

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.has_deprecated_config_parameter.return_value = False
        mock_scm().has_local_branch.side_effect = GitFlowTestV1.side_effect_release_branch
        mock_scm().has_remote_branch.side_effect = GitFlowTestV1.side_effect_release_branch
        mock_configparser().get_project_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"]
        mock_semver().get_version.return_value = \
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]}-rc.1'
        mock_semver().get_final_version.return_value = \
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]

        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing project release candidate creation for mono repo with v1/new "
                     "config format")
        self.assertTrue(
            gitflow_mono_v1.create_project_rc(
                self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
            )
        )
        mock_semver().get_final_version.assert_called_once()
        mock_scm().has_local_branch.assert_called_with(
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["release_branch_prefix"]}/'
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]}'
        )
        mock_scm().add_branch.assert_called_once_with(
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["release_branch_prefix"]}/'
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]}',
            checkout=True
        )
        #
        mock_semver().update_version_files.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"],
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]}-rc.1'
        )
        mock_configparser().update_project_version.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            f'{self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]}-rc.1',
            version_type=None
        )

        mock_scm().has_local_branch.side_effect = None
        mock_scm().has_remote_branch.side_effect = None
        mock_scm().has_local_branch.return_value = True
        mock_scm().has_remote_branch.return_value = True

        logger.debug("Testing project release candidate branch skip for mono repo with v1/new "
                     "config format")
        self.assertFalse(
            gitflow_mono_v1.create_project_rc(
                self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
            )
        )

    @patch.object(GitFlow, 'create_project_rc')
    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_release_candidate_flow(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_project_rc
    ):
        logger.info("Executing unit tests for 'GitFlow.release_candidate_flow' method")

        logger.debug("Initializing GitFlow object for multi repo with v1/new config format")
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["multi"]["v1"]
        mock_semver().get_final_version.side_effect = [
            project["version"].split("-")[0] for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]
        ]
        mock_project_rc.return_value = True
        gitflow_multi_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=True
        )
        gitflow_multi_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing release candidate flow from development branch for multi repo with v1/new "
                     "config format")
        rc_projects = \
            gitflow_multi_v1.release_candidate_flow()

        self.assertCountEqual(
            rc_projects,
            [project_dict["path"] for project_dict in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
        )
        project_rc_calls = [call(
            project["path"]
        ) for project in self.TEST_GITFLOW_CONFIGS["multi"]["v1"]["projects"]]
        mock_project_rc.assert_has_calls(project_rc_calls)
        mock_scm().commit_changes.assert_called_once_with(
            ConventionalCommits.DEFAULT_VERSION_COMMIT,
            f"{self.TEST_REPO_DIRECTORY}/{self.TEST_GITFLOW_CONFIG_FILE}",
            *rc_projects,
            push=True
        )

    @patch.object(GitFlow, "update_version_history")
    @patch("src.comet.work_flows.ConfigParser", autospec=True)
    @patch("src.comet.work_flows.Scm", autospec=True)
    @patch("src.comet.work_flows.SemVer", autospec=True)
    def test_upgrade_stable_branch_project_version(
            self,
            mock_semver,
            mock_scm,
            mock_configparser,
            mock_version_history
    ):
        logger.info("Executing unit tests for 'GitFlow.upgrade_stable_branch_project_version' method")

        logger.debug("Initializing GitFlow object for mono repo with v1/new config format")
        current_stable_version = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0]
        new_stable_version = \
            f'{".".join(self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0].split(".")[:-1])}.' \
            f'{int(self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["version"].split("-")[0].split(".")[-1]) + 1}'
        mock_configparser.return_value.config = self.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.has_deprecated_config_parameter.return_value = False
        mock_scm().find_new_commits.return_value = ["fix_hash"]
        mock_scm().get_commit_message.side_effect = GitFlowTestV1.side_effect_get_commit_message
        mock_scm().get_commit_hexsha.return_value = "fix_hash"
        mock_configparser().get_project_version.return_value = current_stable_version
        mock_semver().get_version.return_value = new_stable_version
        mock_version_history.update_version_history.return_value = False
        gitflow_mono_v1 = GitFlow(
            scm_provider=self.TEST_GIT_CONFIG["scm_providers"][0],
            connection_type=self.TEST_GIT_CONFIG["connection_types"][0],
            username=self.TEST_GIT_CONFIG["username"],
            password=self.TEST_GIT_CONFIG["password"],
            ssh_private_key_path=self.TEST_GIT_CONFIG["ssh_key_path"],
            project_local_path=self.TEST_REPO_DIRECTORY,
            project_config_path=self.TEST_GITFLOW_CONFIG_FILE,
            push_changes=False
        )
        gitflow_mono_v1.prepare_versioning(reference_version_type=None)

        logger.debug("Testing stable branch versioning flow without version history for mono repo with v1/new "
                     "config format")
        stable_upgrade = gitflow_mono_v1.upgrade_stable_branch_project_version(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            latest_bump_commit_hash=None
        )
        self.assertTrue(
            stable_upgrade
        )
        mock_scm().find_new_commits.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["stable_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["development_branch"],
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
        )
        mock_semver().update_version_files.assert_called_once_with(
            current_stable_version,
            new_stable_version
        )
        mock_configparser().update_project_version.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            new_stable_version,
            version_type=None
        )
        mock_version_history.update_version_history.assert_not_called()

        logger.debug("Testing stable branch versioning flow with version history for mono repo with v1/new "
                     "config format")
        mock_version_history.reset_mock()
        mock_version_history.update_version_history.return_value = True
        stable_upgrade = gitflow_mono_v1.upgrade_stable_branch_project_version(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            latest_bump_commit_hash="dummy_hash"
        )
        print(dir(stable_upgrade))
        self.assertTrue(
            stable_upgrade
        )

        mock_version_history.update_version_history.assert_called_once_with(
            self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"],
            "fix_hash",
            "patch"
        )

        # mock_scm().has_local_branch.side_effect = None
        # mock_scm().has_remote_branch.side_effect = None
        # mock_scm().has_local_branch.return_value = True
        # mock_scm().has_remote_branch.return_value = True
        #
        # logger.debug("Testing project release candidate branch skip for mono repo with v1/new "
        #              "config format")
        # self.assertFalse(
        #     gitflow_mono_v1.create_project_rc(
        #         self.TEST_GITFLOW_CONFIGS["mono"]["v1"]["projects"][0]["path"]
        #     )
        # )


if __name__ == '__main__':
    unittest.main()