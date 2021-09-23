import logging
import requests
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.ssh_exception import AuthenticationException, SSHException
import os
import socket
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError, GitError
from .utilities import CometUtilities

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.ERROR)
logging.getLogger("git").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


class ScmException(Exception):
    def __init__(self, msg):
        self.msg = msg


class Scm(object):
    """Backend to handle interaction with Source Code Management (SCM) Provider.

    This SCM backend handles interaction with the Git-based SCM provider.

    By default, it supports:
        - `HTTPS` and `SSH` connections types
        - `Bitbucket` SCM provider

    Example:

    .. code-block:: python

        scm = Scm(
                scm_provider="bitbucket",
                connection_type="https",
                username="dummy",
                password="test",
                repo="test_repo",
                workspace="test_workspace",
                repo_local_path="test_repo",
                ssh_private_key_path="~/.ssh/id_rsa",
                development_branch="develop",
                stable_branch="master"
        )

    .. important::
        All the Git operations are done locally on the specified Git repository using the `git` libraries without any
        SCM provided APIs. It is advised to only utilize SCM provided APIs for operations specific to the individual
        SCM providers.

    :cvar SUPPORTED_SCM_CONNECTION_TYPES: Supported connection types for Git-based SCM providers
    :cvar SUPPORTED_SCM_PROVIDERS: Supported Git-based SCM providers
    """

    SUPPORTED_SCM_CONNECTION_TYPES: list = [
        "ssh",
        "https"
    ]

    SUPPORTED_SCM_PROVIDERS: dict = {
        "bitbucket": {
            "ssh_username": "git",
            "urls": [
                "bitbucket.org",
                "bitbucket.com"
            ]
        }
    }

    def __init__(
            self,
            connection_type: str = "https",
            scm_provider: str = "bitbucket",
            username: str = "",
            password: str = "",
            ssh_private_key_path: str = "~/.ssh/id_rsa",
            repo: str = "",
            workspace: str = "",
            repo_local_path: str = "./",
            stable_branch: str = "master",
            development_branch: str = "develop",
            source_branch: str = ""
    ) -> None:
        """
        Initialize a new SCM class and returns None.
        Initialization includes SCM class pre-checks, repository URL generation and local repository preparation.
        Pre-checks include checking if all the required attributes are provided with supported values only, a valid
        SSH public key exists locally if SSH connection type is requested.
        Repository URL generation step includes generation of a valid repository URL according to the provided
        attributes.
        Local repository preparation checks if the local directory for repository exists and is a valid Git repository
        or clones the repository locally if it doesn't exist.

        :param connection_type: Type of Git connection (Supported: `https`, `ssh`)
        :param scm_provider: Source Code Management Provider name (Supported: `bitbucket`)
        :param username: Username for the user with write access to the project/repository
        :param password: Password for the user with write access to the project/repository
        :param ssh_private_key_path: SSH private key file path on the local machine with write access to the project/repository
        :param repo: Target repository name
        :param workspace: Workspace/username with target repository
        :param repo_local_path: Repository path on the local machine
        :param stable_branch: Stable branch name on the repository
        :param development_branch: Development branch name on the repository
        :param source_branch: Source/target branch name on the repository
        :return: None
        :raises AssertionError:
            raises an exception for missing required attributes or invalid attributes, failed SCM upstream server/s
            lookup and failed Git branches validation
        :raises GitError: raises an exception for failed attempt to clone the Repository from upstream SCM provider
        """
        self.connection_type = connection_type
        self.scm_provider = scm_provider
        self.username = username
        self.password = password
        self.ssh_private_key_path = ssh_private_key_path
        self.repo = repo
        self.workspace = workspace
        self.repo_local_path = repo_local_path
        self.stable_branch = stable_branch
        self.development_branch = development_branch
        self.source_branch = source_branch
        self.repo_url = None
        self.repo_object = None
        self._pre_checks()
        self.generate_repo_url()
        self.prepare_repo()

    def _pre_checks(self) -> None:
        """
        Pre-checks performs the following checks:

            * All the provided attributes' values satisfy the supported values
            * All the required attributes are provided
            * Valid SSH private key exists locally if SSH connection type is requested.

        Additionally, it also converts the provided repository path to an absolute path.

        :return: None
        """
        assert self.connection_type in self.SUPPORTED_SCM_CONNECTION_TYPES, \
            "Invalid connection type [%s] specified! Supported values are [%s]" % (
                self.connection_type,
                ",".join(self.SUPPORTED_SCM_CONNECTION_TYPES)
            )
        assert self.workspace, "Git workspace/username [workspace] variable not provided!"
        assert self.repo, "Git repository name [repo] variable not provided!"
        assert self.scm_provider in list(self.SUPPORTED_SCM_PROVIDERS.keys()), \
            "Invalid SCM provider [%s] specified! Supported values are [%s]" % (
                self.scm_provider,
                ",".join(list(self.SUPPORTED_SCM_PROVIDERS.keys()))
            )
        if self.connection_type == "ssh":
            self._validate_ssh_private_key()
        self.repo_local_path = os.path.abspath(self.repo_local_path)

    def _validate_ssh_private_key(self) -> None:
        """
        Validates the provided SSH private key file path.

        :return: None
        :raises ScmException: raises an exception if the SSH private key file is empty or invalid or doesn't exist
        """
        try:
            logger.debug(f"Validating SSH private key at [{os.path.expanduser(self.ssh_private_key_path)}]")
            RSAKey.from_private_key_file(os.path.expanduser(self.ssh_private_key_path))
            logger.info(f"SSH private key successfully found at the provided file path [{self.ssh_private_key_path}]")
        except IndexError as err:
            logger.debug(err)
            raise ScmException(f"SSH private key [{self.ssh_private_key_path}] is empty!")
        except FileNotFoundError as err:
            logger.debug(err)
            raise ScmException(f"SSH private key [{self.ssh_private_key_path}] file not found!")
        except SSHException as err:
            logger.debug(err)
            raise ScmException(f"SSH private key [{self.ssh_private_key_path}] is invalid!")

    def get_supported_providers(self) -> list:
        """
        Helper method to return a list of supported SCM providers' names.

        :return: List of supported SCM providers
        :rtype: list
        """
        return list(self.SUPPORTED_SCM_PROVIDERS.keys())

    def _validate_scm_provider_server(self, url: str) -> bool:
        """
        Validates the accessibility to the provided SCM provider URL over the requested connection type.

        :param url: Target SCM provider URL
        :return: True or False for the provided SCM provider URL
        :rtype: bool
        :raises requests.exceptions.RequestException: raises an exception if the URL connection over HTTPS fails
        :raises AuthenticationException, SSHException, socket.gaierror:
            raises an exception if the URL connection over SSH fails
        """
        try:
            if self.connection_type == "https":
                url = "https://%s" % url
                http_client = requests.get(url)
                http_client.raise_for_status()
                return True
            elif self.connection_type == "ssh":
                ssh_client = SSHClient()
                ssh_client.set_missing_host_key_policy(AutoAddPolicy())
                ssh_client.connect(
                    hostname=url,
                    username=self.SUPPORTED_SCM_PROVIDERS["bitbucket"]["ssh_username"],
                    key_filename=os.path.expanduser(self.ssh_private_key_path)
                )
                return True
        except requests.exceptions.RequestException as err:
            logger.warning(f"Failed to connect to the SCM provider server [{url}] over {self.connection_type.upper()}")
            logger.debug(f"Exception Message [{url}]: {err}")
            return False
        except (AuthenticationException, SSHException, socket.gaierror) as err:
            logger.warning(f"Failed to connect to the SCM provider server [{url}] over {self.connection_type.upper()}")
            logger.debug(f"Exception Message [{url}]: {err}")
            return False

    def _select_scm_provider_base_url(self) -> [str, None]:
        """
        Selects an active URL for SCM provider from the list of provided URLs.

        :return: Returns a URL if found or None otherwise
        :rtype: str or None
        """
        for url in self.SUPPORTED_SCM_PROVIDERS[self.scm_provider]['urls']:
            if self._validate_scm_provider_server(url):
                return url
        return None

    def _check_repo_local_path_status(self) -> bool:
        """
        Validates if the local repository path has a valid Git project.
        :return: Returns `True` or `False` if the local path is a valid Git project or not
        :rtype: bool
        :raises InvalidGitRepositoryError, NoSuchPathError:
            raises an exception if the specified local repository path is not a valid Git project
        """
        try:
            Repo(self.repo_local_path)
            logger.info(f"Successfully found a Git repository at the specified path [{self.repo_local_path}]")
            return True
        except (InvalidGitRepositoryError, NoSuchPathError) as err:
            logger.warning(f"The specified repository path [{self.repo_local_path}] is not a valid Git repository")
            return False

    def _validate_repo_local_path(self) -> None:
        """
        Checks if the provided local repository path contains the requested Git repository.

        :return: None
        :raises ScmException: raises an exception if the local repository path has a different Git repository
        """
        try:
            repo_object = Repo(self.repo_local_path)
            assert os.path.basename(repo_object.remotes[0].config_reader.get("url").replace(".git", "")) == self.repo, \
                f"The specified repository path [{self.repo_local_path}] contains a different Git repository"
        except AssertionError as err:
            raise ScmException(err)

    def _validate_branches(self) -> bool:
        """
        Appends remote alias if the branches doesn't exist locally and validates if the provided Git branches exist
        on the remote/upstream Git repository.
        It checks the following branches:
            * Stable branch
            * Development branch
            * Source branch

        :return: Returns `True` if the provided branches exist locally or on remote/upstream Git repository or `False`
                 otherwise
        :rtype: bool
        """
        try:
            if not self.source_branch:
                logger.warning(
                    f"Source branch is not specified. Setting source branch to the current active branch [{self.get_active_branch()}]",
                )
                self.source_branch = self.get_active_branch()
            local_branches = [str(branch) for branch in self.repo_object.branches]
            remote_branches = [str(i) for i in self.repo_object.remotes[self.get_remote_alias()].refs]
            if self.stable_branch not in local_branches:
                logger.debug(
                    f"Stable branch [{self.stable_branch}] not found locally. "
                    f"Adding remote alias [{self.get_remote_alias()}] to the stable branch name "
                    f"[{self.get_remote_alias()}/{self.stable_branch}]")
                self.stable_branch = f"{self.get_remote_alias()}/{self.stable_branch}"
                assert self.stable_branch in remote_branches, \
                    "Stable branch [%s] does not exist on remote [%s]" % (
                        self.stable_branch,
                        self.get_remote_alias()
                    )
            if self.development_branch not in local_branches:
                logger.debug(
                    f"Development branch [{self.development_branch}] not found locally. "
                    f"Adding remote alias [{self.get_remote_alias()}] to the stable branch name "
                    f"[{self.get_remote_alias()}/{self.development_branch}]")
                self.development_branch = f"{self.get_remote_alias()}/{self.development_branch}"
                assert self.development_branch in remote_branches, \
                    "Development branch [%s] does not exist on remote [%s]" % (
                        self.development_branch,
                        self.get_remote_alias()
                    )
            if self.source_branch not in local_branches:
                logger.debug(
                    f"Stable branch [{self.source_branch}] not found locally. "
                    f"Adding remote alias [{self.get_remote_alias()}] to the stable branch name "
                    f"[{self.get_remote_alias()}/{self.source_branch}]")
                assert self.source_branch in remote_branches, \
                    "Source branch [%s] does not exist on remote [%s]" % (
                        self.development_branch,
                        self.get_remote_alias()
                    )
            return True
        except AssertionError as err:
            logger.debug(err)
            return False

    def generate_repo_url(self) -> str:
        """
        Generates a remote Git repository URL according to the provided attributes and active SCM URL.
        Validates that both username and password are provided if one of them is specified.

        :return: Generated remote repository URL
        :rtype: str
        :raises AssertionError: raises an exception if no active SCM provider URL is found
        """
        try:
            base_url = self._select_scm_provider_base_url()
            assert base_url, \
                "Please verify your internet connection and accessibility of the SCM provider servers. " \
                "Enable debug mode or manually check the servers using the internet browser or 'ssh' command. " \
                "Check the following SCM provider server URLs: [%s]." % (
                    ",".join(self.SUPPORTED_SCM_PROVIDERS[self.scm_provider]['urls'])
                )
            if self.connection_type == "https":
                if self.username or self.password:
                    assert self.username, "Please provide the Git username!"
                    assert self.password, "Please provide the Git password!"
                    self.repo_url = "%s://%s:%s@%s/%s/%s" % (
                        self.connection_type,
                        self.username,
                        self.password,
                        base_url,
                        self.workspace,
                        self.repo
                    )
                else:
                    self.repo_url = "%s://%s/%s/%s" % (
                        self.connection_type,
                        base_url,
                        self.workspace,
                        self.repo
                    )
            elif self.connection_type == "ssh":
                self.repo_url = "%s://%s@%s/%s/%s" % (
                    self.connection_type,
                    self.SUPPORTED_SCM_PROVIDERS["bitbucket"]["ssh_username"],
                    base_url,
                    self.workspace,
                    self.repo
                )
            return self.repo_url
        except AssertionError as err:
            logger.error("Failed to find an active/available server for the requested SCM provider [%s]", self.scm_provider)
            logger.debug(err)
            raise

    def prepare_repo(self) -> None:
        """
        Prepares local Git repository directory by making sure that it exists and is a valid Git
        repository with available requested branches locally/remotely. If the Git repository directory
        does not exist, it will clone it from the SCM provider using the generated repository URL.

        :return: None
        :raises GitError: raises an exception if it fails to clone the Git repository from upstream SCM provider
        :raises AssertionError: raises an exception if the requested branches does not exist locally or remotely
        """
        try:
            repo_local_path_status = self._check_repo_local_path_status()
            if repo_local_path_status:
                self._validate_repo_local_path()
            if not repo_local_path_status:
                logger.info(
                    f"Cloning Git repository {self.workspace}/{self.repo}] from "
                    f"remote SCM provider [{self.scm_provider}] server"
                )
                Repo.clone_from(url=self.repo_url, to_path=self.repo_local_path)
            self.repo_object = Repo(self.repo_local_path)
            assert self._validate_branches(), "Git Branches validation failed!"
        except GitError as err:
            logger.error("Failed to clone the Git repository [%s/%s] from remote SCM provider [%s] server",
                            self.workspace,
                            self.repo,
                            self.scm_provider
                            )
            raise
        except AssertionError as err:
            logger.error("Failed to prepare the Git repository [%s/%s] from remote SCM provider [%s] server",
                            self.workspace,
                            self.repo,
                            self.scm_provider
                            )
            raise

    def find_new_commits(self, source_branch: str, reference_branch: str, path: str = ".") -> list:
        """
        Finds new commits for a specified file path in the source branch in comparison to the reference/target branch.
        By default, `path` is set to `.` that will result in finding commits for all files recursively.

        :param source_branch: Source branch name
        :param reference_branch: Reference/target branch name
        :param path: Target file path to find commits for only
        :return: List of new commits found
        :rtype: list
        """
        logger.debug(
            f"Looking for new commits on [{path}] project path on source branch "
            f"[{source_branch}] compared to reference branch [{reference_branch}]")
        commit_range = f"{reference_branch}...{source_branch}"
        commits = [commit for commit in self.repo_object.iter_commits(commit_range, paths=path, reverse=True)]
        return commits

    def commit_changes(self, msg: str = "chore: commit changes", *paths: list, push: bool = False) -> None:
        """
        Commits changes for a specified file path/s with an optional flag to push changes to the upstream or remote
        Git repository.

        :param msg:
            Git commit message string. This defaults to a `chore: commit changes` which is a `chore` type commit message
            according to the Conventional Commits Specification
        :param paths: Path/s to be added in the commit
        :param push: Enables pushing commits to the remote/upstream Git repository
        :return: None
        :raises GitError:
            raises an exception if it fails to make Git commit changes locally or fails to push the local changes to
            the upstream/remote
        """
        try:
            repo_changed_files = [item.a_path for item in self.repo_object.index.diff(None)]
            project_staged_files = [path for path in paths if path in repo_changed_files]
            if len(project_staged_files) > 0:
                logger.info(f"Committing path/s [{[path for path in paths]}] changes")
                self.repo_object.git.add(paths)
                self.repo_object.git.commit("-m", msg)
                if push:
                    self.push_changes(branch=self.get_active_branch())
            else:
                logger.warning(f"No commits found for project files {','.join(paths)}")
        except GitError as err:
            logger.debug(err)
            raise

    def get_remote_alias(self) -> str:
        """
        Fetches the locally set Git remote alias. For example, `origin`.

        :return: Remote Git alias for the tracked/referenced
        :rtype: str
        """
        return str(self.repo_object.remote())

    def get_active_branch(self) -> str:
        """
        Fetches the locally active/checked out Git branch.

        :return: Active/Checked out local Git branch
        :rtype: str
        """
        return str(self.repo_object.active_branch)

    def get_active_branch_hex(self) -> str:
        """
        Fetches the 40 Bytes Hex version for SHA-1 hash of the locally active/checked out Git branch.

        :return: 40 Bytes Hex for the active/checked out local Git branch hash
        :rtype: str
        """
        return str(self.repo_object.active_branch.object.hexsha)

    @CometUtilities.unstable_function_warning
    def get_latest_tag(self) -> None:
        """
        Fetches the latest Git tag found locally.

        :return: Git tag name
        :rtype: str
        """
        tag = None
        if len(self.repo_object.tags) > 0:
            tag = str(self.repo_object.tags[-1])
        return tag

    @CometUtilities.unsupported_function_error
    def show_file(self, branch: str, file: str) -> str:
        try:
            logger.debug(f"Executing Git show command for a [{file}] file on [{branch}] branch")
            output = self.repo_object.git.show(f"{branch}:{file}")
            return output
        except GitError as err:
            logger.debug(err)
            raise

    @CometUtilities.unsupported_function_error
    def add_tag(self, name: str) -> None:
        """
        Adds a Git tag in the local Git repository.

        :param name: Git tag name
        :return: None
        """
        pass

    def add_branch(self, branch: str, checkout: bool = False) -> None:
        """
        Adds a Git branch in the local Git repository and optionally checkout to the newly created branch.

        :param branch: Git branch name
        :param checkout: Enables checking out to the newly Git branches
        :return: None
        :raises GitError:
            raises an exception if it fails to create Git branch locally or fails to checkout to the newly created
            Git branch
        """
        try:
            logger.info(f"Creating a Git branch [{branch}]")
            new_branch = self.repo_object.create_head(branch)
            if checkout:
                new_branch.checkout()
        except GitError as err:
            logger.debug(err)
            raise

    @CometUtilities.unstable_function_warning
    def merge_branches(self, source_branch: str, destination_branch: str, msg: str = None) -> None:
        """
        Merge Git branches locally with the specified Git message.

        :param source_branch: Source Git branch name
        :param destination_branch: Destination Git branch name
        :param msg: Git merge message string
        :return: None
        :raises GitError:
            raises an exception if it fails to merge the source Git branch into destination Git branch
        """
        try:
            logger.debug(f"Merging source branch [{source_branch}] into destination branch [{destination_branch}]")
            source_branch = self.repo_object.heads[source_branch]
            destination_branch = self.repo_object.heads[destination_branch]
            self.repo_object.git.checkout(destination_branch)
            self.repo_object.git.merge(source_branch)
            # merge_base = self.repo_object.merge_base(source_branch, destination_branch)
            # self.repo_object.index.merge_tree(destination_branch, base=merge_base)
            # self.repo_object.index.commit(f"chore: merge '{source_branch}' into '{destination_branch}')",
            #                               parent_commits=(source_branch.commit, destination_branch.commit))
            self.repo_object.git.checkout(source_branch)
        except GitError as err:
            logger.debug(err)
            raise

    def push_changes(self, branch: str = None) -> None:
        """
        Push local Git changes to the remote/upstream Git repository from an optional specific source Git branch.

        :param branch: Source Git branch name
        :return: None
        :raises GitError:
            raises an exception if it fails to push changes to the remote/upstream Git repository
        """
        try:
            logger.info(f"Pushing local changes to remote [{self.get_remote_alias()}]")
            self.repo_object.remote().push(branch)
        except GitError as err:
            logger.debug(err)
            raise
