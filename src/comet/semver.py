import logging
from semver.version import Version
import os
import re
from .config import ConfigParser

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.ERROR)
logging.getLogger("git").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

class SemVer(object):

    MAJOR = 4
    MINOR = 3
    PATCH = 2
    PRE_RELEASE = 1
    NO_CHANGE = 0

    SUPPORTED_RELEASE_TYPES = {
        MAJOR: "major",
        MINOR: "minor",
        PATCH: "patch",
        PRE_RELEASE: "pre_release",
        NO_CHANGE: "no_change"
    }

    # SUPPORTED_RELEASE_TYPES = [
    #     "major",
    #     "minor",
    #     "patch",
    #     "pre_release"
    # ]

    SUPPORTED_PRE_RELEASE_TYPES = [
        "dev",
        "alpha",
        "beta",
        "rc"
    ]

    DEFAULT_VERSION_FILE = ".comet.yml"

    def __init__(
            self,
            project_path: str = ".",
            version_files: list = [],
            version_regex: str = ""
    ):
        self.project_path = os.path.normpath(project_path)
        self.version_files = version_files
        self.version_regex = version_regex
        self.version_object = None
        self.default_version_file_path = self.DEFAULT_VERSION_FILE
        self.release_version = None
        self.current_version = None
        self._pre_checks()
        self.prepare_version()

    def _pre_checks(self):
        self._sanitize_version_file_paths()
        assert self._validate_version_files(), "Version files validation failed!"
        assert self._validate_project_path(), "Project path validation failed!"

    def _sanitize_version_file_paths(self):
        logger.debug(f"Sanitizing version files paths according to the project directory [{self.project_path}]")
        self.version_files = [os.path.normpath(f"{self.project_path}/{file}") for file in self.version_files]
        self.default_version_file_path = os.path.normpath(f"{self.project_path}/{self.DEFAULT_VERSION_FILE}")

    def _validate_default_version_file(self):
        try:
            assert os.path.exists(self.default_version_file_path), \
                f"Default Version file [{self.default_version_file_path}] not found!"
            Version.parse(self._read_default_version_file())
            return True
        except (ValueError, AssertionError) as err:
            logger.debug(err)
            return False

    def _validate_release_type(self, release: int):
        try:
            assert release in list(self.SUPPORTED_RELEASE_TYPES.keys()), \
                f"Invalid release type [{release}({self.SUPPORTED_RELEASE_TYPES[release]})] specified! " \
                f"Supported values are [{','.join([str(i) for i in self.SUPPORTED_RELEASE_TYPES.keys()])}]"
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    def _validate_pre_release_type(self, pre_release):
        try:
            assert pre_release in self.SUPPORTED_PRE_RELEASE_TYPES, \
                f"Invalid pre-release type [{pre_release}] specified! " \
                f"Supported values are [{','.join(self.SUPPORTED_PRE_RELEASE_TYPES)}]"
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    def _initialize_default_version_file(self, version="0.1.0-dev.1"):
        try:
            with open(self.default_version_file_path, 'a') as f:
                f.write(version)
            return True
        except OSError as err:
            logger.debug(err)
            return False

    def _read_default_version_file(self):
        try:
            project_config = ConfigParser(
                config_path=self.default_version_file_path
            )
            project_config.read_config()
            return project_config.get_project_version(self.project_path)
        except OSError as err:
            logger.debug(err)
            raise

    def _update_default_version_file(self):
        try:
            project_config = ConfigParser(
                config_path=self.default_version_file_path
            )
            project_config.read_config()
            project_config.update_project_version(self.project_path, self.get_version())
        except OSError as err:
            logger.debug(err)
            raise

    def _validate_version_files(self):
        try:
            for file in self.version_files:
                assert os.path.exists(file), "Version file [%s] not found!" % file
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    def _validate_project_path(self):
        try:
            assert os.path.exists(self.project_path), f"Sub-project [{self.project_path}] directory not found!"
            assert os.path.isdir(self.project_path), f"Sub-project [{self.project_path}] must be of type directory!"
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    def _validate_version_files_consistency(self):
        pass

    def get_version(self):
        return str(self.version_object)

    # TODO: Add comet config initialization
    def prepare_version(self):
        try:
            if not self._validate_default_version_file():
                # assert self._initialize_default_version_file(), "Default version file initialization failed!"
                pass
            version = self._read_default_version_file()
            self.version_object = Version.parse(version)
        except (ValueError, AssertionError) as err:
            logger.error(
                f"Failed to prepare the version using default version file [{self.default_version_file_path}]"
            )
            logger.debug(err)
            raise

    def compare_bumps(self, current_bump: int, next_bump: int) -> int:
        try:
            assert self._validate_release_type(current_bump), "Release type validation failed!"
            assert self._validate_release_type(next_bump), "Release type validation failed!"
            if next_bump > current_bump:
                return next_bump
            elif next_bump <= current_bump:
                return self.PRE_RELEASE
        except AssertionError as err:
            logger.error(
                f"Failed to compare the bumps for version [{self.get_version()}]"
            )
            logger.debug(err)
            raise

    def bump_version(self, release=PRE_RELEASE, pre_release=None):
        try:
            assert self._validate_release_type(release), "Release type validation failed!"
            if pre_release:
                assert self._validate_pre_release_type(pre_release), "Pre-release type validation failed!"
            if release == self.MAJOR:
                self.version_object = self.version_object.bump_major()
            elif release == self.MINOR:
                self.version_object = self.version_object.bump_minor()
            elif release == self.PATCH:
                self.version_object = self.version_object.bump_patch()
            elif release == self.PRE_RELEASE:
                self.version_object = self.version_object.bump_prerelease(pre_release)
            if pre_release and release in [self.MAJOR, self.MINOR, self.PATCH]:
                self.version_object = self.version_object.bump_prerelease(pre_release)
        except AssertionError as err:
            logger.error(
                f"Failed to bump the version [{self.get_version()}]"
            )
            logger.debug(err)
            raise

    # def _update_version_string_in_file(self, file: str, current_version: str, new_version):
    #     with open(file, "r+") as f:
    #         data = f.read()
    #         data = re.sub(current_version, new_version, data)
    #         f.seek(0)
    #         f.write(data)
    #         f.truncate()

    def update_version_files(self):
        try:
            current_version = self._read_default_version_file()
            new_version = self.get_version()
            logger.info(f"Updating version files to the new version [{new_version}]")
            for file in self.version_files:
                logger.debug(f"Updating the version file [{file}]")
                with open(file, "r+") as f:
                    data = f.read()
                    data = re.sub(f"{self.version_regex}{current_version}", f"{self.version_regex}{new_version}", data)
                    f.seek(0)
                    f.write(data)
                    f.truncate()
            logger.debug(f"Updating the default version file [{self.default_version_file_path}]")
            self._update_default_version_file()
        except OSError as err:
            logger.debug(err)
            return False

    # def get_version_diff(self, source_version, reference_version):
