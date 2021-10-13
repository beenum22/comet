import logging
from semver.version import Version
import os
import re
from .config import ConfigParser
from .utilities import CometUtilities

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.ERROR)
logging.getLogger("git").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


class SemVer(object):
    """
    Backend to handle versioning for a project according to Semantic Versioning Specification.

    This SemVer backend handles versioning for a project according to Semantic Versioning Specification. The idea is
    to have a class that handles all the Semantic Versioning related operations for the requested project. This class
    depends on `ConfigParser` class and is only supposed to be used with Comet too. It can be used with other tools if
    they follow the Comet philosophy or design.

    The SemVer object can read the reference version in the main project version file (.comet.yml usually), bump it
    according to the requested type of version bump and update the main project version file. Since, it depends on
    the Comet design, it can use two types of reference versions: `dev` and `stable`.
    This SemVer object also supports updating project specific version file paths using the provided regex pattern.

    .. important::
        Semver instance represents one project version only.

    Example:

    .. code-block:: python

        semver = SemVer(
            project_path=".",
            version_files=["VERSION"],
            version_regex="",
            project_version_file=".comet.yml",
            reference_version_type="stable"
        )

    :cvar MAJOR: Numerical representation for Major type of version bump/release
    :cvar MINOR: Numerical representation for Minor type of version bump/release
    :cvar PATCH: Numerical representation for Patch type of version bump/release
    :cvar PRE_RELEASE: Numerical representation for pre-release type of version bump/release
    :cvar BUILD: Numerical representation for build type of version bump/release
    :cvar NO_CHANGE: Numerical representation for skipping the version bump/release
    :cvar SUPPORTED_RELEASE_TYPES:
        Types of supported releases with respective names according to Semantic Versioning spec
    :cvar SUPPORTED_PRE_RELEASE_TYPES:
        Types of supported pre-release identifiers
    :cvar DEFAULT_VERSION_FILE:
        Default project file name.
        It is set to `.comet.yml` as the SemVer object is developed for Comet primarily.
    """

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
    ) -> None:
        """
        Initialize a new SemVer class.
        Initialization includes SemVer class pre-checks, repository URL generation and local repository preparation.
        Pre-checks include checking if all the required attributes are provided with supported values only, a valid
        SSH public key exists locally if SSH connection type is requested.
        Repository URL generation step includes generation of a valid repository URL according to the provided
        attributes.
        Local repository preparation checks if the local directory for repository exists and is a valid Git repository
        or clones the repository locally if it doesn't exist.

        :param project_path: Target project directory path
        :param version_files: List of additional version file paths for the target project
        :param version_regex: Regex pattern to use while replacing the version in additional project version files
        :param project_version_file:
            Main project version file path. Defaults to Comet configuration file `.comet.yml`.
        :param reference_version_type: Reference version to use from the Comet configuration file
        :return: None
        :raises AssertionError:
            raises an exception if the pre-checks and version preparation fails
        """
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

    def _pre_checks(self) -> None:
        """
        Sanitizes/Normalizes all the file paths according to the root project directory and validates the project
        directory path and existence project specific version files

        :return: None
        :raises AssertionError:
            raises an exception if project directory doesn't exist or project specific version files are missing.
        """
        self._sanitize_version_file_paths()
        assert self._validate_version_files(), "Version files validation failed!"
        assert self._validate_project_path(), "Project path validation failed!"

    def _sanitize_version_file_paths(self) -> None:
        """
        Sanitizes/Normalizes all the file paths according to the root project directory. It appends root project
        path to all the file paths and removes redundant separators from the all the file paths.

        File paths include the main project version file and project specific version files.

        :return: None
        """
        logger.debug(f"Sanitizing version files paths according to the project directory [{self.project_path}]")
        self.version_files = [os.path.normpath(f"{self.project_path}/{file}") for file in self.version_files]
        self.project_version_file = os.path.normpath(f"{self.project_version_file}")

    def _validate_default_version_file(self) -> bool:
        """
        Validates the existence of main/default project version file and the reference version found in it.

        :return: Returns `True` if the validation is successful and `False` otherwise
        """
        try:
            assert os.path.exists(self.project_version_file), \
                f"Default Version file [{self.project_version_file}] not found!"
            Version.parse(self._read_default_version_file())
            return True
        except (ValueError, AssertionError) as err:
            logger.debug(err)
            return False

    def _validate_release_type(self, release: int) -> bool:
        """
        Validates the release type according to the supported release types.

        :param release: Numerical representation of the release type according to :cvar::`SUPPORTED_RELEASE_TYPES`
        :return: Returns `True` if the validation is successful and `False` otherwise
        """
        try:
            assert release in list(self.SUPPORTED_RELEASE_TYPES.keys()), \
                f"Invalid release type [{release}({self.SUPPORTED_RELEASE_TYPES[release]})] specified! " \
                f"Supported values are [{','.join([str(i) for i in self.SUPPORTED_RELEASE_TYPES.keys()])}]"
            return True
        except (AssertionError, KeyError) as err:
            logger.debug(err)
            return False

    def _validate_reference_version_type(self) -> None:
        """
        Validates the reference version type according to the supported reference version types specified in
        :cvar::`SUPPORTED_REFERENCE_VERSION_TYPES`.

        :return: None
        :raises AssertionError: raises an exception if unsupported reference version type is provided
        """
        assert self.reference_version_type in list(self.SUPPORTED_REFERENCE_VERSION_TYPES), \
            f"Invalid reference version type" \
            f"[{self.reference_version_type}({self.SUPPORTED_REFERENCE_VERSION_TYPES})] specified! " \
            f"Supported values are [{','.join([str(i) for i in self.SUPPORTED_REFERENCE_VERSION_TYPES])}]"

    def _validate_pre_release_type(self, pre_release: str) -> bool:
        """
        Validates the pre-release identifier according to the supported pre-release identifiers specified in
        :cvar::`SUPPORTED_PRE_RELEASE_TYPES`.

        :param pre_release: Pre-release identifier
        :return: Returns `True` if the validation is successful and `False` otherwise
        """
        try:
            assert pre_release in self.SUPPORTED_PRE_RELEASE_TYPES, \
                f"Invalid pre-release type [{pre_release}] specified! " \
                f"Supported values are [{','.join(self.SUPPORTED_PRE_RELEASE_TYPES)}]"
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    @CometUtilities.unsupported_function_error
    def _initialize_default_version_file(self, version: str = "0.1.0-dev.1") -> bool:
        """
        Validates the pre-release identifier according to the supported pre-release identifiers specified in
        :cvar::`SUPPORTED_PRE_RELEASE_TYPES`.

        :param version: Initialized version string
        :return: Returns `True` if the version file initialized successfully and `False` otherwise
        """
        try:
            with open(self.project_version_file, 'a') as f:
                f.write(version)
            return True
        except OSError as err:
            logger.debug(err)
            return False

    def _read_default_version_file(self, version_type: str = "stable") -> str:
        """
        Fetches the reference version string from the main/default project version file.

        :param version_type:
            Reference version type. Default is set to `stable`.
        :return: Reference version string
        :raises OSError:
            raises an exception if it fails to read the reference version from the main/default project version file.
        """
        try:
            project_config = ConfigParser(
                config_path=self.project_version_file
            )
            project_config.read_config()
            return project_config.get_project_version(self.project_path, version_type=version_type)
        except OSError as err:
            logger.debug(err)
            raise

    def _update_default_version_file(self, version: str, version_type: str = "dev") -> None:
        """
        Updates the specified reference version type in the main/default project version file according to the latest
        version generated by SemVer instance.

        :param version_type:
            Reference version type. Default is set to `dev`.
        :return: None
        :raises OSError:
            raises an exception if it fails to write/update the reference version in the main/default project version
            file.
        """
        try:
            project_config = ConfigParser(
                config_path=self.project_version_file
            )
            project_config.read_config()
            project_config.update_project_version(self.project_path, version, version_type)
        except OSError as err:
            logger.debug(err)
            raise

    def _validate_version_files(self) -> bool:
        """
        Validates if the project specific version files exist.

        :return: Returns `True` if the validation is successful and `False` otherwise
        """
        try:
            for file in self.version_files:
                assert os.path.exists(file), "Version file [%s] not found!" % file
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    def _validate_project_path(self) -> bool:
        """
        Validates if the project directory exists.

        :return: Returns `True` if the validation is successful and `False` otherwise
        """
        try:
            assert os.path.exists(self.project_path), f"Sub-project [{self.project_path}] directory not found!"
            assert os.path.isdir(self.project_path), f"Sub-project [{self.project_path}] must be of type directory!"
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    @CometUtilities.unsupported_function_error
    def _validate_version_files_consistency(self) -> None:
        """
        Validates if the versions are consistent between the main/default project version file and project specific
        version files.

        :return: Returns `True` if the validation is successful and `False` otherwise
        """
        pass

    def get_version(self) -> str:
        """
        Fetches the current project version generated/parsed by the SemVer instance.

        :return: Current version string
        """
        return str(self.version_object)

    def get_final_version(self) -> str:
        """
        Fetches the current project version generated/parsed by the SemVer instance without any pre-release identifiers
        and metadata.

        :return: Finalized current version string without pre-release identifier and metadata
        """
        return str(self.version_object.finalize_version())

    # TODO: Add comet config initialization
    def prepare_version(self) -> None:
        """
        Prepares the current project version for bumps/releases by making sure it follows the Semantic Versioning
        Specification.

        :return: None
        :raises ValueError, AssertionError:
            raises an exception if it fails to prepare the current reference project version for new releases/bumps
        """
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
        """
        Compares the two version bump/release types and returns a valid bump/release type.

        If the next version bump/ release is higher than the current version bump/release, it will bump/release the
        next version according to the new version bump/release specified in :param:`next_bump`.

        If the next version bump/release is less than or equal to the current version bump/release, it will set the
        next version bump/release to pre-release type.

        For example:
            * Scenario 1:
                Last version = 1.0.1-dev.1

                Last bump/release to the version was Patch type (current_bump = 3)

                Next bump/release to the version is found to be Minor type (next_bump = 4)

                It will return `4` which means next bump/release has to be the Minor type.

                Next version = 1.1.0-dev.1

            * Scenario 2:
                Last version = 2.1.1-dev.1

                Last bump/release to the version was Minor type (current_bump = 4)

                Next bump/release to the version is found to be Patch type (next_bump = 3)

                It will return `2` which means next bump/release has to be the Pre-release type.

                Next version = 2.1.1-dev.2

            * Scenario 2:
                Last version = 3.1.1-dev.1

                Last bump/release to the version was Minor type (current_bump = 4)

                Next bump/release to the version is found to be Minor type (next_bump = 4)

                It will return `2` which means next bump/release has to be the Pre-release type.

                Next version = 3.1.1-dev.2

        :param current_bump: Current/Last bump/release type performed
        :param next_bump: Next bump/release type according to the change found
        :return: Next bump/release type to perform for version upgrade
        :raises AssertionError:
            raises an exception if incorrect/unsupported bump types are provided
        """
        try:
            assert self._validate_release_type(current_bump), "Release type validation failed!"
            assert self._validate_release_type(next_bump), "Release type validation failed!"
            assert next_bump != self.NO_CHANGE, "No change is specified as next bump/release!"
            if next_bump > current_bump:
                return next_bump
            elif next_bump <= current_bump != self.BUILD:
                return self.PRE_RELEASE
            elif next_bump <= current_bump == self.BUILD:
                return self.BUILD
        except AssertionError as err:
            logger.error(
                f"Failed to compare the bumps for version [{self.get_version()}]"
            )
            logger.debug(err)
            raise

    # TODO: Allow changing pre_release type for versions with pre_release defined
    # TODO: Add pre-release type validation
    def bump_version(
            self,
            release: int = PRE_RELEASE,
            pre_release: str = None,
            build_metadata: str = None,
            static_build_metadata: bool = False
    ) -> None:
        """
        Upgrades the version according to the type bump/release specified with optional pre-release and build metadata.

        Example:
            * Scenario 1:
                Current version = 0.1.0
                Release type = Minor (:param:`release`)
                Pre-release type = 'dev' (:param:`pre_release`)
                Build Metadata = None (:param:`build_metadata`)
                Static Build Metadata = False (:param:`static_build_metadata`)

                Upgraded version = 0.2.0-dev.1

            * Scenario 2:
                Current version = 0.2.0-dev.1
                Release type = Pre-release (:param:`release`)
                Pre-release type = 'dev' (:param:`pre_release`)
                Build Metadata = None (:param:`build_metadata`)
                Static Build Metadata = False (:param:`static_build_metadata`)

                Upgraded version = 0.2.0-dev.2

            * Scenario 3:
                Current version = 0.2.0-dev.2
                Release type = Build (:param:`release`)
                Pre-release type = None (:param:`pre_release`) (No effect on Build metadata)
                Build Metadata = 'dummy_metadata' (:param:`build_metadata`)
                Static Build Metadata = False (:param:`static_build_metadata`)

                Upgraded version = 0.2.0-dev.2+dummy_metadata.1

            * Scenario 4:
                Current version = 0.2.0-dev.2
                Release type = Build (:param:`release`)
                Pre-release type = None (:param:`pre_release`) (No effect on Build metadata)
                Build Metadata = 'dummy_metadata' (:param:`build_metadata`)
                Static Build Metadata = True (:param:`static_build_metadata`)

                Upgraded version = 0.2.0-dev.2+dummy_metadata

            * Scenario 5:
                Current version = 0.2.0-dev.2+dummy_metadata
                Release type = Minor (:param:`release`)
                Pre-release type = None (:param:`pre_release`)
                Build Metadata = 'dummy_metadata' (:param:`build_metadata`) (No effect on Major, Minor and Patch)
                Static Build Metadata = True (:param:`static_build_metadata`) (No effect on Major, Minor and Patch)

                Upgraded version = 0.3.0

        :param release: Bump/release type (Integer representation) for version upgrade
        :param pre_release: Optional type of pre-release identifier to append to the version
        :param build_metadata: Optional build metadata to append to the version
        :param static_build_metadata: Optional flag to have static build metadata without any incremental section
        :return: None
        :raises AssertionError:
            raises an exception if it fails to upgrade the version
        """
        try:
            assert self._validate_release_type(release), "Release type validation failed!"
            if pre_release or release == self.PRE_RELEASE:
                assert self._validate_pre_release_type(pre_release), \
                    f"Invalid Pre-release type [{pre_release}] is provided!"
            if release == self.MAJOR:
                self.version_object = self.version_object.bump_major()
            elif release == self.MINOR:
                self.version_object = self.version_object.bump_minor()
            elif release == self.PATCH:
                self.version_object = self.version_object.bump_patch()
            elif release == self.PRE_RELEASE:
                if self.version_object.prerelease and pre_release != self.version_object.prerelease.split('.')[0]:
                    self.version_object = self.version_object.finalize_version()
                self.version_object = self.version_object.bump_prerelease(pre_release)
            elif release == self.BUILD:
                assert build_metadata, "No Build metadata is provided!"
                if static_build_metadata:
                    self.version_object = self.version_object.replace(build=build_metadata)
                else:
                    self.version_object = self.version_object.bump_build(build_metadata)
            if pre_release and release in [self.MAJOR, self.MINOR, self.PATCH]:
                self.version_object = self.version_object.bump_prerelease(pre_release)
        except AssertionError as err:
            logger.error(
                f"Failed to bump the version [{self.get_version()}]"
            )
            logger.debug(err)
            raise

    # TODO: Raise an error if it fails to update the version files
    def update_version_files(self, old_version: str, new_version: str) -> None:
        """
        Updates the default/main project version file and project specific version files according to the latest
        version set in the SemVer instance.

        :param old_version: Old/current version string to look for in the files
        :param new_version: New version string update in the files
        :return: None
        :raises OSError:
            raises an exception if it fails to update the version files
        """
        try:
            logger.info(f"Updating version files to the new version [{new_version}]")
            for file in self.version_files:
                logger.debug(f"Updating the version file [{file}]")
                with open(file, "r+") as f:
                    data = f.read()
                    if self.version_regex:
                        regex = re.compile(self.version_regex)
                        if regex.groups > 2:
                            logger.warning(f"Only first captured group in the regular expressions will be used while "
                                           f"substituting the version string in files")
                        data = re.sub(f"{regex}", f"\g<1>{new_version}", data)
                    else:
                        data = re.sub(f"{old_version}", f"{new_version}", data)
                    f.seek(0)
                    f.write(data)
                    f.truncate()
        except OSError as err:
            logger.debug(err)
            return False
