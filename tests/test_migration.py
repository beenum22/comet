import unittest
from unittest import TestCase
from unittest import TestCase
from unittest.mock import patch, mock_open
import logging

# from .common import TestBaseConfig
# from src.comet.migration import MigrationHelper

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class TestMigrationHelper(TestCase):
    def test_migrate_deprecated_config(self):
        self.fail()

    def test_migrate_state_backend(self):
        self.fail()
