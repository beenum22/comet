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

    MAJOR = 5
    MINOR = 4
    PATCH = 3
    PRE_RELEASE = 2
    BUILD = 1
    NO_CHANGE = 0

    SUPPORTED_RELEASE_TYPES = {
        MAJOR: "major",
        MINOR: "minor",
        PATCH: "patch",
        PRE_RELEASE: "pre_release",
        BUILD: "build",
        NO_CHANGE: "no_change"
    }

    SUPPORTED_PRE_RELEASE_TYPES = [
        "dev",
        "alpha",
        "beta",
        "rc"
    ]

    SUPPORTED_REFERENCE_VERSION_TYPES = [
        "stable",
        "dev"
    ]

    DEFAULT_VERSION_FILE = ".comet.yml"

    def __init__(
            self,
            project_path: str = ".",
            version_files: list = [],
            version_regex: str = "",
            project_version_file: str = DEFAULT_VERSION_FILE,
            reference_version_type: str = "stable"
    ):
        self.project_path = os.path.normpath(project_path)
        self.version_files = version_files
        self.version_regex = version_regex
        self.version_object = None
        self.project_version_file = project_version_file
        self.reference_version_type = reference_version_type
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
        self.project_version_file = os.path.normpath(f"{self.project_version_file}")

    def _validate_default_version_file(self):
        try:
            assert os.path.exists(self.project_version_file), \
                f"Default Version file [{self.project_version_file}] not found!"
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

    def _validate_reference_version_type(self):
        assert self.reference_version_type in list(self.SUPPORTED_REFERENCE_VERSION_TYPES), \
            f"Invalid reference version type" \
            f"[{self.reference_version_type}({self.SUPPORTED_REFERENCE_VERSION_TYPES})] specified! " \
            f"Supported values are [{','.join([str(i) for i in self.SUPPORTED_REFERENCE_VERSION_TYPES])}]"

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
            with open(self.project_version_file, 'a') as f:
                f.write(version)
            return True
        except OSError as err:
            logger.debug(err)
            return False

    def _read_default_version_file(self, version_type: str = "stable"):
        try:
            project_config = ConfigParser(
                config_path=self.project_version_file
            )
            project_config.read_config()
            return project_config.get_project_version(self.project_path, version_type=version_type)
        except OSError as err:
            logger.debug(err)
            raise

    def _update_default_version_file(self, version_type: str = "dev"):
        try:
            project_config = ConfigParser(
                config_path=self.project_version_file
            )
            project_config.read_config()
            project_config.update_project_version(self.project_path, self.get_version(), version_type)
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
            self._validate_reference_version_type()
            if not self._validate_default_version_file():
                # assert self._initialize_default_version_file(), "Default version file initialization failed!"
                pass
            self.version_object = Version.parse(self._read_default_version_file(version_type=self.reference_version_type))
        except (ValueError, AssertionError) as err:
            logger.error(
                f"Failed to prepare the version using default version file [{self.project_version_file}]"
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

    def bump_version(self, release: int = PRE_RELEASE, pre_release: str = None, build_metadata: str = None):
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
            elif release == self.BUILD:
                self.version_object = self.version_object.bump_build(build_metadata)
            if pre_release and release in [self.MAJOR, self.MINOR, self.PATCH]:
                self.version_object = self.version_object.bump_prerelease(pre_release)
        except AssertionError as err:
            logger.error(
                f"Failed to bump the version [{self.get_version()}]"
            )
            logger.debug(err)
            raise

    def update_version_files(self, version: str):
        try:
            new_version = self.get_version()
            logger.info(f"Updating version files to the new version [{new_version}]")
            for file in self.version_files:
                logger.debug(f"Updating the version file [{file}]")
                with open(file, "r+") as f:
                    data = f.read()
                    data = re.sub(f"{re.escape(self.version_regex + version)}", f"{self.version_regex}{new_version}", data)
                    f.seek(0)
                    f.write(data)
                    f.truncate()
            logger.debug(f"Updating the default version file [{self.project_version_file}]")
            self._update_default_version_file()
        except OSError as err:
            logger.debug(err)
            return False

    # def get_version_diff(self, source_version, reference_version):
