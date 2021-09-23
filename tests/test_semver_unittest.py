import unittest
from unittest.mock import patch
import logging

from src.comet.semver import SemVer

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class SemVerTest(unittest.TestCase):
    TEST_DEV_VERSION = "0.1.0-dev.1"
    TEST_STABLE_VERSION = "0.1.0"
    TEST_DIRECTORY = "test_project"
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
                "path": TEST_DIRECTORY,
                "stable_version": TEST_STABLE_VERSION,
                "dev_version": TEST_DEV_VERSION,
                "version_regex": "",
                "version_files": [
                    TEST_PROJECT_VERSION_FILE
                ]
            }
        ]
    }

    @patch("src.comet.semver.ConfigParser")
    @patch('src.comet.semver.os')
    def test_compare_bumps(
            self,
            mock_os,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.compare_bumps' method")

        mock_configparser.return_value.config = self.TEST_PROJECT_CONFIG
        mock_configparser.return_value.get_project_version.return_value = self.TEST_DEV_VERSION

        semver = SemVer(
            project_path=SemVerTest.TEST_DIRECTORY,
            version_files=[
                SemVerTest.TEST_PROJECT_VERSION_FILE
            ],
            version_regex="",
            project_version_file=SemVerTest.TEST_PROJECT_CONFIG_FILE,
            reference_version_type="stable"
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
    @patch('src.comet.semver.os')
    def test_bump_version(
            self,
            mock_os,
            mock_configparser
    ):
        logger.info("Executing unit tests for 'SemVer.bump_version' method")

        mock_configparser.return_value.config = self.TEST_PROJECT_CONFIG
        mock_configparser.return_value.get_project_version.return_value = self.TEST_DEV_VERSION

        semver = SemVer(
            project_path=SemVerTest.TEST_DIRECTORY,
            version_files=[
                SemVerTest.TEST_PROJECT_VERSION_FILE
            ],
            version_regex="",
            project_version_file=SemVerTest.TEST_PROJECT_CONFIG_FILE,
            reference_version_type="stable"
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
        with self.assertRaises(AssertionError):
            semver.bump_version(
                release=10,
                pre_release=None,
                build_metadata=None,
                static_build_metadata=False
            )

        logger.debug("Testing pre-release type exception handling")
        with self.assertRaises(AssertionError):
            semver.bump_version(
                release=semver.MINOR,
                pre_release="muneeb",
                build_metadata=None,
                static_build_metadata=False
            )
        logger.debug("Testing Build metadata string exception handling")
        with self.assertRaises(AssertionError):
            semver.bump_version(
                release=semver.BUILD,
                pre_release=None,
                build_metadata=None,
                static_build_metadata=False
            )


if __name__ == '__main__':
    unittest.main()
