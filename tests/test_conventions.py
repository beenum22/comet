import unittest
import logging

from .common import TestBaseCommitMessages
from src.comet.conventions import ConventionalCommits
from src.comet.semver import SemVer

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


# TODO: Remove mention of ng-voice in any form
class ConventionalCommitsTest(unittest.TestCase):

    def test_lint_commit(self):
        logger.info("Executing unit tests for 'ConventionalCommits.lint_commit' method")

        logger.debug("Testing major feature commit message")
        self.assertTrue(
            ConventionalCommits.lint_commit(TestBaseCommitMessages.BREAKING_FEAT_MSG)
        )

        logger.debug("Testing minor feature commit message")
        self.assertTrue(
            ConventionalCommits.lint_commit(TestBaseCommitMessages.FEAT_MSG)
        )

        logger.debug("Testing patch commit message")
        self.assertTrue(
            ConventionalCommits.lint_commit(TestBaseCommitMessages.FIX_MSG)
        )

        logger.debug("Testing Invalid message 1")
        self.assertFalse(
            ConventionalCommits.lint_commit(TestBaseCommitMessages.INVALID_MSG_1)
        )

        logger.debug("Testing Invalid message 2")
        self.assertFalse(
            ConventionalCommits.lint_commit(TestBaseCommitMessages.INVALID_MSG_2)
        )

    def test_ignored_commit(self):
        logger.info("Executing unit tests for 'ConventionalCommits.ignored_commit' method")
        logger.debug("Testing Merge commit message")
        self.assertTrue(
            ConventionalCommits.ignored_commit(TestBaseCommitMessages.MERGE_MSG)
        )

        logger.debug("Testing chore commit message")
        self.assertTrue(
            ConventionalCommits.ignored_commit(TestBaseCommitMessages.CHORE_MSG)
        )

        logger.debug("Testing valid commit message")
        self.assertFalse(
            ConventionalCommits.ignored_commit(TestBaseCommitMessages.FEAT_MSG)
        )

    def test_get_bump_type(self):
        logger.info("Executing unit tests for 'ConventionalCommits.get_bump_type' method")

        logger.debug("Testing bump type for major/breaking change commit")
        self.assertEqual(
            ConventionalCommits.get_bump_type(TestBaseCommitMessages.BREAKING_FEAT_MSG),
            SemVer.MAJOR
        )

        logger.debug("Testing bump type for minor change commit")
        self.assertEqual(
            ConventionalCommits.get_bump_type(TestBaseCommitMessages.FEAT_MSG),
            SemVer.MINOR
        )

        logger.debug("Testing bump type for patch change commit")
        self.assertEqual(
            ConventionalCommits.get_bump_type(TestBaseCommitMessages.FIX_MSG),
            SemVer.PATCH
        )


if __name__ == '__main__':
    unittest.main()