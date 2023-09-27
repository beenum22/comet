import unittest
from unittest.mock import patch, mock_open
import logging

from .common import TestBaseConfig
from src.comet.semver import SemVer

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class SemVerTest(unittest.TestCase):

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    def test_get_version_enum_value(
            self,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.get_version_enum_value' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        semver = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )

        logger.debug("Testing enum output for valid version bump names")
        self.assertEqual(semver.get_version_enum_value("major"), semver.MAJOR)
        self.assertEqual(semver.get_version_enum_value("minor"), semver.MINOR)
        self.assertEqual(semver.get_version_enum_value("patch"), semver.PATCH)

        logger.debug("Testing enum output for invalid version bump names")
        self.assertEqual(semver.get_version_enum_value("awesome"), semver.NO_CHANGE)

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    def test_get_version(
            self,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.get_version' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        semver = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )

        logger.debug("Testing version output string")
        self.assertEqual(semver.get_version(), TestBaseConfig.TEST_DEV_VERSION)

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    def test_get_final_version(
            self,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.get_final_version' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        semver = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )

        logger.debug("Testing final or stable version output string")
        self.assertEqual(semver.get_final_version(), TestBaseConfig.TEST_STABLE_VERSION)

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    def test_prepare_version(
            self,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.prepare_version' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        logger.debug("Testing versioning object preparation for v1/new Comet configuration format")
        SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    def test_compare_bumps(
            self,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.compare_bumps' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        semver = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )

        logger.debug("Testing valid version bumps comparison")
        self.assertEqual(semver.compare_bumps(semver.MINOR, semver.MAJOR), semver.MAJOR)
        self.assertEqual(semver.compare_bumps(semver.PATCH, semver.MINOR), semver.MINOR)
        self.assertEqual(semver.compare_bumps(semver.PATCH, semver.PATCH), semver.PRE_RELEASE)
        self.assertEqual(semver.compare_bumps(semver.MAJOR, semver.MINOR), semver.PRE_RELEASE)
        self.assertEqual(semver.compare_bumps(semver.BUILD, semver.BUILD), semver.BUILD)
        self.assertEqual(semver.compare_bumps(semver.NO_CHANGE, semver.PATCH), semver.PATCH)

        logger.debug("Testing incorrect current bump exception handling")
        with self.assertRaises(AssertionError):
            semver.compare_bumps(10, 4)
        logger.debug("Testing incorrect next bump exception handling")
        with self.assertRaises(AssertionError):
            semver.compare_bumps(4, 10)
        logger.debug("Testing no change type next bump exception handling")
        with self.assertRaises(AssertionError):
            semver.compare_bumps(1, 0)

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    def test_bump_version(
            self,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.bump_version' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        semver = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )

        semver.bump_version(
            release=semver.MINOR,
            pre_release=None,
            build_metadata=None,
            static_build_metadata=False
        )
        self.assertEqual(semver.get_version(), "0.2.0")

        semver.bump_version(
            release=semver.MINOR,
            pre_release="dev",
            build_metadata=None,
            static_build_metadata=False
        )
        self.assertEqual(semver.get_version(), "0.3.0-dev.1")

        semver.bump_version(
            release=semver.PRE_RELEASE,
            pre_release="dev",
            build_metadata=None,
            static_build_metadata=False
        )
        self.assertEqual(semver.get_version(), "0.3.0-dev.2")

        semver.bump_version(
            release=semver.PRE_RELEASE,
            pre_release="rc",
            build_metadata=None,
            static_build_metadata=False)
        self.assertEqual(semver.get_version(), "0.3.0-rc.1")

        semver.bump_version(
            release=semver.BUILD,
            pre_release="rc",
            build_metadata="dummy_metadata",
            static_build_metadata=False
        )
        self.assertEqual(semver.get_version(), "0.3.0-rc.1+dummy_metadata.1")

        semver.bump_version(
            release=semver.BUILD,
            pre_release="rc",
            build_metadata="dummy_metadata",
            static_build_metadata=True
        )
        self.assertEqual(semver.get_version(), "0.3.0-rc.1+dummy_metadata")

        semver.bump_version(
            release=semver.PATCH,
            pre_release="beta",
            build_metadata="dummy_metadata",
            static_build_metadata=True
        )
        self.assertEqual(semver.get_version(), "0.3.1-beta.1")

        semver.bump_version(
            release=semver.MAJOR,
            pre_release=None,
            build_metadata=None,
            static_build_metadata=False
        )
        self.assertEqual(semver.get_version(), "1.0.0")

        logger.debug("Testing release type exception handling")
        with self.assertRaises(Exception):
            semver.bump_version(
                release=10,
                pre_release=None,
                build_metadata=None,
                static_build_metadata=False
            )

        logger.debug("Testing pre-release type exception handling")
        with self.assertRaises(Exception):
            semver.bump_version(
                release=semver.MINOR,
                pre_release="muneeb",
                build_metadata=None,
                static_build_metadata=False
            )
        logger.debug("Testing Build metadata string exception handling")
        with self.assertRaises(Exception):
            semver.bump_version(
                release=semver.BUILD,
                pre_release=None,
                build_metadata=None,
                static_build_metadata=False
            )

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os.path.isdir')
    @patch('src.comet.semver.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=f"Version: {str(TestBaseConfig.TEST_DEV_VERSION)}")
    def test_update_version_files(
            self,
            mock_update,
            mock_os_exists,
            mock_os_isdir,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.update_version_files' method")

        mock_configparser.return_value.config = TestBaseConfig.TEST_GITFLOW_CONFIGS["mono"]["v1"]
        mock_configparser.return_value.get_project_version.return_value = TestBaseConfig.TEST_DEV_VERSION

        logger.debug(
            "Testing version files update using regex pattern with one capturing group for v1/new Comet "
            "configuration format"
        )
        semver_v1_with_one_group_regex = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )
        semver_v1_with_one_group_regex.update_version_files(
            TestBaseConfig.TEST_DEV_VERSION, f"{semver_v1_with_one_group_regex.get_final_version()}"
        )
        for version_file in semver_v1_with_one_group_regex.version_files:
            mock_update.assert_called_with(version_file, "r+")
            handle = mock_update()
            handle.write.assert_called_once_with(f"Version: {semver_v1_with_one_group_regex.get_final_version()}")

        mock_update.reset_mock()

        logger.debug(
            "Testing version files update without version regex pattern for v1/new Comet configuration format"
        )
        semver_v1_without_regex = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex="",
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )
        semver_v1_without_regex.update_version_files(
            TestBaseConfig.TEST_DEV_VERSION, semver_v1_without_regex.get_final_version()
        )
        for version_file in semver_v1_without_regex.version_files:
            mock_update.assert_called_with(version_file, "r+")
            handle = mock_update()
            handle.write.assert_called_once_with(f"Version: {semver_v1_without_regex.get_final_version()}")

        mock_update.reset_mock()

        logger.debug(
            "Testing version files update using regex pattern with two capturing group for v1/new Comet "
            "configuration format"
        )
        semver_v1_with_zero_group_regex = SemVer(
            project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
            version_files=[
                TestBaseConfig.TEST_PROJECT_VERSION_FILE
            ],
            version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ZERO_GROUP,
            reference_version=TestBaseConfig.TEST_DEV_VERSION
        )
        semver_v1_with_zero_group_regex.update_version_files(
            TestBaseConfig.TEST_DEV_VERSION, f"{semver_v1_with_zero_group_regex.get_final_version()}"
        )
        for version_file in semver_v1_with_zero_group_regex.version_files:
            mock_update.assert_called_with(version_file, "r+")
            handle = mock_update()
            handle.write.assert_called_once_with(f"{semver_v1_with_zero_group_regex.get_final_version()}")

        logger.debug("Testing version files update exception handling")
        with self.assertRaises(Exception):
            semver_v1_with_one_group_regex = SemVer(
                project_path=TestBaseConfig.TEST_REPO_DIRECTORY,
                version_files=[
                    TestBaseConfig.TEST_PROJECT_VERSION_FILE
                ],
                version_regex=TestBaseConfig.TEST_PROJECT_VERSION_REGEX_ONE_GROUP,
                reference_version=TestBaseConfig.TEST_DEV_VERSION
            )
            mock_update.side_effect = OSError()
            semver_v1_with_one_group_regex.update_version_files(
                TestBaseConfig.TEST_DEV_VERSION, f"{semver_v1_with_one_group_regex.get_final_version()}"
            )


if __name__ == '__main__':
    unittest.main()
