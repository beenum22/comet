import unittest
import logging

from src.comet.conventions import ConventionalCommits

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class ConventionalCommitsTest(unittest.TestCase):

    BREAKING_FEAT_MSG = """feat(pcscf,cscf_controller): add p-cscf to cscf controller

This change enables the PCSCF to be controlled by the CSCF controller. It also enables the PCSCF to have an extra interface which it then uses to interact with the Packet Core network. This feature adds the following features

* Add MacVLAN / SRIOV interface on P-CSCF
* Remove privileged container in P-CSCF
* Make external network configurable
* Adds resource limits for SRIOV
* Remove headless service creation for P-CSCF
* Remove lifecycle hooks for P-CSCF as it is now managed by CSCF controller

BREAKING CHANGE: If the new controller is not deployed the P-CSCF is not able to be managed by the CSCF controller.
Merges-PR #21
Approved-by: Behnam Hooshiarkashani
Approved-by: Muneeb Ahmad"""

    FEAT_MSG = """feat(srvcc): add a new ansible role srvcc

SUMMARY OF CHANGES:
This PR adds the role SRVCC for automated deployment over a kubernetes cluster. It includes deployment of SRVCC as a CSCF object, required configmaps and services and destruction of these objects upon destroy command

WHAT THIS PR DOES:
It adds an ansible role to deploy SRVCC over a kubernetes cluster
The network design and details of communication can be seen in
https://ng-voice.atlassian.net/wiki/spaces/~575210533/pages/edit-v2/763363350?draftShareId=8c6c444a-848b-4eaa-91cb-eaacf8a61239

WHICH TICKETS THIS PR CATERS FOR
https://ng-voice.atlassian.net/browse/CLD-402

Merges-PR #53
Merged-by: Muhammad Zeeshan
Approved by: Abdul Basit Alvi and Akin Ozer"""

    FIX_MSG = """fix(scscf): add missing jsonrpc configuration for s-cscf

SUMMARY OF CHANGES

Adds missing JSON RPC configuration to S-CSCF configuration.

WHAT THIS PR DOES
This PR adds a bugfix in S-CSCF Kamailio configuration where JSON RPC configuration is missing. After this PR change, `WITH_JSONRPC` is set in the main Kamailio configuration when JSON RPC is enabled using `scscf_jsonrpc` variable.

ADDED VARIABLES
n/a

WHICH ISSUE(S) THIS PR FIXES
https://ng-voice.atlassian.net/browse/CLD-411?atlOrigin=eyJpIjoiYjY4YWI0MDMwNTYwNDU3NDkwMDM2ZWFkOWQ3NzViNDciLCJwIjoiaiJ9

Merges-PR #48
Merged-by: Muneeb Ahmad
Approved-by: Muhammad Zeeshan
Approved-by: Behnam Hooshiarkashani"""

    MERGE_MSG = """Merge in release/2021.1 (pull request #110)

Release/2021.1 merge to develop

Approved-by: Rick Barenthin"""

    CHORE_MSG = """chore: auto update comet config and project version files"""

    INVALID_MSG_1 = """dummy(test): this is an invalid message
No space is provided between title and body
Test body
No space is provided between body and footer
Merged-by: Muneeb Ahmad"""

    INVALID_MSG_2 = """TEST(test)= this is an invalid message
    
Test body
    
Merged-by: Muneeb Ahmad"""

    def test_lint_commit(self):
        logger.info("Executing unit tests for 'ConventionalCommits.lint_commit' method")

        logger.debug("Testing major feature commit message")
        self.assertTrue(
            ConventionalCommits.lint_commit(self.BREAKING_FEAT_MSG)
        )

        logger.debug("Testing minor feature commit message")
        self.assertTrue(
            ConventionalCommits.lint_commit(self.FEAT_MSG)
        )

        logger.debug("Testing patch commit message")
        self.assertTrue(
            ConventionalCommits.lint_commit(self.FIX_MSG)
        )

        logger.debug("Testing Invalid message 1")
        self.assertFalse(
            ConventionalCommits.lint_commit(self.INVALID_MSG_1)
        )

        logger.debug("Testing Invalid message 2")
        self.assertFalse(
            ConventionalCommits.lint_commit(self.INVALID_MSG_2)
        )

    def test_ignored_commit(self):
        logger.info("Executing unit tests for 'ConventionalCommits.ignored_commit' method")
        logger.debug("Testing Merge commit message")
        self.assertTrue(
            ConventionalCommits.ignored_commit(self.MERGE_MSG)
        )

        logger.debug("Testing chore commit message")
        self.assertTrue(
            ConventionalCommits.ignored_commit(self.CHORE_MSG)
        )

        logger.debug("Testing valid commit message")
        self.assertFalse(
            ConventionalCommits.ignored_commit(self.FEAT_MSG)
        )


if __name__ == '__main__':
    unittest.main()