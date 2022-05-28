import logging
import requests
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.ssh_exception import AuthenticationException, SSHException
import os
import re
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


# TODO: Add to check to make sure remote URL is according to the requested Git connection type
# TODO: Fail if it fails to push changes to the remote due to invalid permissions
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
        },
        "github": {
            "ssh_username": "git",
            "urls": [
                "github.com"
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
            configure_remote: bool = False
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
        :param configure_remote: Optional flag to configure remote repository
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
        self.configure_remote = configure_remote
        self.repo_url = None
        self.repo_object = None
        self._pre_checks()
        if self.configure_remote:
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
        # TODO: Add check to make sure no file is changed in the local repo
        if self.configure_remote:
            assert self.connection_type in self.SUPPORTED_SCM_CONNECTION_TYPES, \
                f"Invalid connection type {self.connection_type} specified! Supported values are " \
                f"{','.join(self.SUPPORTED_SCM_CONNECTION_TYPES)}"
            assert self.scm_provider in list(self.SUPPORTED_SCM_PROVIDERS.keys()), \
                f"Invalid SCM provider {self.scm_provider} specified! Supported values are " \
                f"{','.join(list(self.SUPPORTED_SCM_PROVIDERS.keys()))}"
            if self.connection_type == "ssh":
                self._validate_ssh_private_key()
        assert self.workspace, "Git workspace/username [workspace] variable not provided!"
        assert self.repo, "Git repository name [repo] variable not provided!"
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
        Checks if the provided local repository path contains the requested Git repository with remotes configured.

        :return: None
        :raises ScmException:
            raises an exception if the local repository path has a different Git repository or no remote/upstream
            Git repositories are configured.
        """
        try:
            repo_object = Repo(self.repo_local_path)
            # TODO: Remove redundant commented out lines
            # assert repo_object.git_dir, \
            #     f"The specified local directory is not a valid Git repository. " \
            #     f"Configure a valid Git repository first."
            # assert len(repo_object.remotes) > 0, \
            #     f"The specified Git repository has no remote/upstream repositories configured. " \
            #     f"Configure valid Git remote/upstream URLs first."
            # assert os.path.basename(repo_object.remotes[0].config_reader.get("url").replace(".git", "")) == self.repo, \
            #     f"The specified repository path [{self.repo_local_path}] contains a different Git repository or " \
            #     f"invalid Git remote/upstream URLs are configured"
        except AssertionError as err:
            raise ScmException(err)

    def get_supported_providers(self) -> list:
        """
        Helper method to return a list of supported SCM providers' names.

        :return: List of supported SCM providers
        :rtype: list
        """
        return list(self.SUPPORTED_SCM_PROVIDERS.keys())

    @CometUtilities.unstable_function_warning
    def has_local_reference(self, reference: str) -> bool:
        """
        Checks if the requested Git reference exists in the Git repository.

        :param reference: Local Git reference name
        :return: `True` if the requested Git reference exists locally in the Git repository or `False` otherwise
        """
        local_references = [str(ref) for ref in self.repo_object.refs]
        if reference in local_references:
            logger.debug(f"Git reference [{reference}] exists in the local Git repository")
            return True
        logger.debug(f"Git reference [{reference}] does not exist in the local Git repository")
        return False

    @CometUtilities.unstable_function_warning
    def has_local_branch(self, branch: str) -> bool:
        """
        Checks if the requested branch exists in the Git repository.

        :param branch: Local Git branch name
        :return: `True` if the requested branch exists locally in the Git repository or `False` otherwise
        """
        local_branches = [str(local_branch) for local_branch in self.repo_object.branches]
        if branch in local_branches:
            logger.debug(f"Git branch [{branch}] exists in the local Git repository")
            return True
        logger.debug(f"Git branch [{branch}] does not exist in the local Git repository")
        return False

    @CometUtilities.unstable_function_warning
    def has_remote_branch(self, branch: str) -> bool:
        """
        Checks if the requested branch exists in the remote Git repository.

        :param branch: Remote Git branch name
        :return: `True` if the requested branch exists in the remote Git repository or `False` otherwise
        """
        if self.has_remote_alias_configured(self.get_remote_alias()):
            remote_branches = [
                str(remote_branch) for remote_branch in self.repo_object.remote(self.get_remote_alias()).refs
            ]
            if branch in remote_branches:
                logger.debug(f"Git branch [{branch}] exists in the local Git repository")
                return True
            logger.debug(f"Git branch [{branch}] does not exist in the local Git repository")
            return False
        return False

    @CometUtilities.unstable_function_warning
    def has_remote_alias_configured(self, alias: str) -> bool:
        """
        Checks if the requested remote alias/upstream repository is configured for the Git repository.

        :param alias: Git remote alias/upstream repository name
        :return: `True` if the requested remote alias is configured for the Git repository or `False` otherwise
        """
        try:
            return self.repo_object.remote(alias).exists()
        except ValueError:
            return False

    def _strip_remote_alias(self, branch: str) -> str:
        """
        Removes remote alias prefix from the branch.

        This method is required when pushing changes to the remote branch.
        :param branch: Git branch name
        :return: Git branch name without remote alias prefix
        """
        logger.debug(f"Stripping remote alias [{self.get_remote_alias()}] from the branch name")
        return re.sub(f"{self.get_remote_alias()}/", "", str(branch))

    def _get_commit_object(self, revision: str):
        """
        Fetch GitPython 'Commit' object for the requested Git revision.

        :param revision: Git revision
        :return: Returns GitPython 'Commit' object for the requested Git revision.
        """
        return self.repo_object.commit(revision)

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
            logger.error("Failed to find an active/available server for the requested SCM provider [%s]",
                         self.scm_provider)
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
                # TODO: Is it revelant considering I need info about remote URL using Comet config, which exists at
                #       root of this repo?
                Repo.clone_from(url=self.repo_url, to_path=self.repo_local_path)
            self.repo_object = Repo(self.repo_local_path)
            logger.debug(
                f"Successfully prepared Git repository [{self.workspace}/{self.repo}]"
                f"{' with remote URL [' + self.repo_url + ']' if self.repo_url else ''}"
            )
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

    def get_commit_message(self, revision: str):
        """
        Fetch commit message for the requested Git revision such as commit hash ID or branch name.

        :param revision: Git revision
        :return: Git commit message for the requested Git revision
        """
        msg = None
        msg = self._get_commit_object(revision).message
        logger.debug(f"Commit message successfully fetched for the requested Git revision [{revision}]")
        return msg

    def get_commit_hexsha(self, revision: str, short=False):
        """
        Fetches 40 Bytes or optional shorter 7 Bytes Hex version for SHA-1 hash for the requested Git revision
        such as commit hash ID or branch name.

        :param revision: Git revision
        :return: Git commit 40 Bytes or 7 Bytes Hex for the requested Git revision
        """
        sha = None
        if short:
            sha_length = 7
            sha = self.repo_object.git.rev_parse(self._get_commit_object(revision).hexsha, short=sha_length)
        else:
            sha = self._get_commit_object(revision).hexsha
        logger.debug(
            f"Commit {'shorter 7 Bytes ' if short else ' '}hexsha successfully fetched for the "
            f"requested Git revision [{revision}]"
        )
        return sha

    # TODO: Replace branch with reference
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
        commits = [commit.hexsha for commit in self.repo_object.iter_commits(commit_range, paths=path, reverse=True)]
        return commits

    # TODO: Check warnings for this method
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
                    self.push_changes(
                        branch=self.get_active_branch(),
                        tags=False
                    )
            else:
                logger.warning(f"No commits found for project files {','.join(paths)}")
        except GitError as err:
            logger.debug(err)
            raise

    def get_remote_alias(self) -> [str, None]:
        """
        Fetches the locally set Git remote alias. For example, `origin`.

        :return: Remote Git alias for the tracked/referenced
        :rtype: str
        """
        try:
            return str(self.repo_object.remote())
        except ValueError:
            return None

    def get_active_branch(self) -> str:
        """
        Fetches the locally active/checked out Git branch.

        :return: Active/Checked out local Git branch
        :rtype: str
        """
        return str(self.repo_object.active_branch)

    @CometUtilities.deprecated_function_warning
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

    @CometUtilities.unstable_function_warning
    def add_tag(self, name: str, strict: bool = False) -> None:
        """
        Adds a Git tag in the local Git repository.

        :param name: Git tag name
        :param strict: Fails if the tag already exists
        :return: None
        """
        try:
            if strict:
                assert name not in self.repo_object.tags, f"Git tag [{name}] already exists in the repository!"
            if name not in self.repo_object.tags:
                logger.info(f"Add Git tag [{name}] to the repository")
                self.repo_object.create_tag(name)
        except (AssertionError, GitError) as err:
            logger.debug(err)
            raise

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
            source_branch = self.repo_object.refs[source_branch]
            destination_branch = self.repo_object.refs[destination_branch]
            self.repo_object.git.checkout(self._strip_remote_alias(destination_branch))
            self.repo_object.git.merge(source_branch)
            # merge_base = self.repo_object.merge_base(source_branch, destination_branch)
            # self.repo_object.index.merge_tree(destination_branch, base=merge_base)
            # self.repo_object.index.commit(f"chore: merge '{source_branch}' into '{destination_branch}')",
            #                               parent_commits=(source_branch.commit, destination_branch.commit))
            self.repo_object.git.checkout(self._strip_remote_alias(source_branch))
        except GitError as err:
            logger.debug(err)
            raise

    def push_changes(self, branch: str = None, tags: bool = False) -> None:
        """
        Push local Git changes to the remote/upstream Git repository from an optional specific source Git branch.

        :param branch: Source Git branch name
        :param tags: Flag to push local Git tags
        :return: None
        :raises GitError:
            raises an exception if it fails to push changes to the remote/upstream Git repository
        """
        try:
            logger.info(f"Pushing local changes to remote [{self.get_remote_alias()}]")
            self.repo_object.remote().push(self._strip_remote_alias(branch), tags=tags)
        except GitError as err:
            logger.debug(err)
            raise

    @CometUtilities.unstable_function_warning
    def add_note(
            self,
            note_ref: str = None,
            notes: str = "",
            object_ref: str = "",
            force: bool = True
    ) -> None:
        """
        Add Git notes at custom notes reference for the target reference object.

        :param note_ref: Custom reference under `.git/refs/notes/` where the Git note will be stored
        :param notes: Notes to store at the specified Git notes reference
        :param object_ref: Target Git reference/object to store notes for
        :param force: Replace existing notes for the target reference/object if it is set

        :return: None
        :raises GitError:
            raises an exception if it fails to create Git notes for the specified Git notes reference and object
        """
        try:
            logger.debug(f"Adding Git note [{notes}] at [{note_ref}] for the target Git reference [{object_ref}]")
            self.repo_object.git.notes(
                f"--ref={note_ref}",
                "add",
                "-m",
                f"{notes}",
                f"{'-f' if force else ''}",
                f"{object_ref}"
            )
        except GitError as err:
            logger.debug(err)
            raise

    @CometUtilities.unstable_function_warning
    def read_note(
            self,
            note_ref: str = None,
            object_ref: str = None,
    ) -> str:
        """
        Fetch Git notes at the specified Git notes reference for the target Git reference/object.

        :param note_ref: Custom reference under `.git/refs/notes/` where the Git note will be stored
        :param object_ref: Target Git reference/object to store notes for

        :return: Git note string
        :raises GitError:
            raises an exception if it fails to fetch Git notes for the specified Git notes reference and object
        """
        try:
            assert self.has_local_reference(reference=note_ref), f"Git notes reference [{note_ref}] doesn't exist in " \
                                                                 f"the local Git repository"
            # assert self.has_local_reference(reference=object_ref), f"Target Git reference [{object_ref}] doesn't exist " \
            #                                                        f"in the local Git repository"
            logger.debug(f"Fetching Git note at [{note_ref}] for the target Git reference [{object_ref}]")
            note = self.repo_object.git.notes(
                f"--ref={note_ref}",
                "show",
                f"{object_ref}"
            )
            logger.debug(f"Git notes: {note}")
            return note
        except (AssertionError, GitError) as err:
            logger.debug(err)
            raise Exception(
                f"Failed to fetch Git note for target [{object_ref}] at the specified Git reference [{note_ref}]"
            )

    @CometUtilities.unstable_function_warning
    def list_notes(
            self,
            note_ref: str = None
    ) -> str:
        """
        List Git notes at the specified Git notes reference.

        :param note_ref: Custom reference under `.git/refs/notes/` where the Git note will be stored

        :return: Git notes list
        :raises GitError:
            raises an exception if it fails to list Git notes for the specified Git notes reference
        """
        try:
            assert self.has_local_reference(reference=note_ref), f"Git notes reference [{note_ref}] doesn't exist in " \
                                                                 f"the local Git repository"
            logger.debug(f"Listing Git notes at [{note_ref}] reference")
            notes = self.repo_object.git.notes(
                f"--ref={note_ref}",
                "list"
            )
            return notes
        except (AssertionError, GitError) as err:
            logger.debug(err)
            raise Exception(
                f"Failed to list Git notes at the specified Git reference [{note_ref}]"
            )

    @CometUtilities.unstable_function_warning
    def remove_note(
            self,
            note_ref: str,
            object_ref: str
    ) -> None:
        """
        List Git notes at the specified Git notes reference.

        :param note_ref: Custom reference under `.git/refs/notes/` where the Git note will be deleted
        :param object_ref: Target Git reference/object to delete notes for

        :return: None
        :raises GitError:
            raises an exception if it fails to remove Git notes for the specified Git notes reference and object
        """
        try:
            assert self.has_local_reference(reference=note_ref), f"Git notes reference [{note_ref}] doesn't exist in " \
                                                                 f"the local Git repository"
            # assert self.has_local_reference(reference=object_ref), f"Target Git reference [{object_ref}] doesn't exist " \
            #                                                        f"in the local Git repository"
            logger.debug(f"Removing Git notes at [{note_ref}] reference for the target Git reference [{object_ref}]")
            self.repo_object.git.notes(
                f"--ref={note_ref}",
                "remove",
                object_ref
            )
        except (AssertionError, GitError) as err:
            logger.debug(err)
            raise Exception(
                f"Failed to remove Git notes for target [{object_ref}] at the specified Git reference [{note_ref}]"
            )
