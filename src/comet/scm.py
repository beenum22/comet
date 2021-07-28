import logging
import requests
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.ssh_exception import AuthenticationException, SSHException
import os
import socket
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError, GitError

logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.ERROR)
logging.getLogger("git").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


class ScmException(Exception):
    def __init__(self, msg):
        self.msg = msg


class Scm(object):

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
    ):
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

    def get_supported_providers(self):
        return list(self.SUPPORTED_SCM_PROVIDERS.keys())

    def _validate_scm_provider_server(self, url: str) -> bool:
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
        for url in self.SUPPORTED_SCM_PROVIDERS[self.scm_provider]['urls']:
            if self._validate_scm_provider_server(url):
                return url
        return None

    def _check_repo_local_path_status(self) -> bool:
        try:
            Repo(self.repo_local_path)
            logger.info(f"Successfully found a Git repository at the specified path [{self.repo_local_path}]")
            return True
        except (InvalidGitRepositoryError, NoSuchPathError) as err:
            logger.warning(f"The specified repository path [{self.repo_local_path}] is not a valid Git repository")
            return False

    def _validate_repo_local_path(self) -> None:
        try:
            repo_object = Repo(self.repo_local_path)
            assert os.path.basename(repo_object.remotes[0].config_reader.get("url").strip(".git")) == self.repo, \
                f"The specified repository path [{self.repo_local_path}] contains a different Git repository"
        except AssertionError as err:
            raise ScmException(err)

    def _validate_branches(self):
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

    def generate_repo_url(self):
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

    def prepare_repo(self) -> bool:
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
            return True
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

    def find_new_commits(self, source_branch, reference_branch, path="."):
        logger.info(
            f"Looking for new commits on [{path}] project path on source branch "
            f"[{source_branch}] compared to reference branch [{reference_branch}]")
        commit_range = f"{reference_branch}...{source_branch}"
        commits = [commit for commit in self.repo_object.iter_commits(commit_range, paths=path, reverse=True)]
        return commits

    def commit_changes(self, msg: str = "chore: commit changes", *paths: list, push: bool = False) -> None:
        try:
            repo_changed_files = [item.a_path for item in self.repo_object.index.diff(None)]
            project_staged_files = [path for path in paths if path in repo_changed_files]
            if len(project_staged_files) > 0:
                logger.info(f"Committing path/s [{[path for path in paths]}] changes")
                self.repo_object.git.add(paths)
                self.repo_object.git.commit("-m", msg)
                if push:
                    self.push_changes()
            else:
                logger.warning(f"No commits found for project files {','.join(paths)}")
        except GitError as err:
            logger.debug(err)
            raise

    def get_remote_alias(self):
        return str(self.repo_object.remote())

    def get_active_branch(self):
        return str(self.repo_object.active_branch)

    def get_active_branch_hex(self):
        return str(self.repo_object.active_branch.object.hexsha)

    def get_latest_tag(self):
        tag = None
        if len(self.repo_object.tags) > 0:
            tag = str(self.repo_object.tags[-1])
        return tag

    def show_file(self, branch: str, file: str) -> str:
        try:
            logger.debug(f"Executing Git show command for a [{file}] file on [{branch}] branch")
            output = self.repo_object.git.show(f"{branch}:{file}")
            return output
        except GitError as err:
            logger.debug(err)
            raise

    def add_tag(self, name):
        pass

    def add_branch(self, branch):
        try:
            logger.info(f"Creating a Git branch [{branch}]")
            self.repo_object.create_head(branch)
        except GitError as err:
            logger.debug(err)
            raise

    def push_changes(self):
        try:
            logger.info(f"Pushing local changes to remote [{self.get_remote_alias()}]")
            self.repo_object.remote().push()
        except GitError as err:
            logger.debug(err)
            raise
