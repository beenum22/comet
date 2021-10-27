#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from .work_flows import GitFlow
from .config import ConfigParser
import logging.config
from colorama import Fore, Style
import coloredlogs

from .work_flows import GitFlow
from .config import ConfigParser

__author__ = 'Muneeb Ahmad'
__version__ = '0.2.0-dev.23'
__license__ = "MIT"
__maintainer__ = "Muneeb Ahmad"
__email__ = "muneeb@ng-voice.com"


def banner():
    print(f"""{Fore.LIGHTMAGENTA_EX}
 ██████╗ ██████╗ ███╗   ███╗███████╗████████╗
██╔════╝██╔═══██╗████╗ ████║██╔════╝╚══██╔══╝
██║     ██║   ██║██╔████╔██║█████╗     ██║   
██║     ██║   ██║██║╚██╔╝██║██╔══╝     ██║   
╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗   ██║   
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝   ╚═╝   
{Style.RESET_ALL}
{Fore.LIGHTWHITE_EX}
Comet is a simple tool to automate/facilitate release cycle.
Happy Versioning!
{Style.RESET_ALL}""")


def main() -> None:
    """
    Main Comet function that is executed to perform all the Comet utility operations.

    Currently, Comet supports only Gitflow-based development cycle and provides the
    `run` flag parameter to execute the supported flows/operations. Supported flows
    are:

      1. Comet configuration initialization (init)
      2. Branch specific versioning handling (branch-flow)
      3. Release candidate branch creation (release-candidate)
      4. Releasing directly to the stable branch (release)
      5. Sync development branch with stable branch (sync)

    Main workflows requires the following variables as pre-requisites:

      1. Git SCM provider name (Default and only supported one: bitbucket)
      2. Git connection type to connect with SCM provider (Default: https)
      3. Git username to access upstream repo hosted by SCM provider (Required if HTTPS Git connection type)
      4. Git password to access upstream repo hosted by SCM provider (Required if HTTPS Git connection type)
      5. SSH key-pair with access to upstream repo hosted by SCM provider (Default: ~/.ssh/id_rsa) (Required if SSH Git connection type)
      6. Comet configuration file name (Default: .comet.yml)
      7. Local Git repository path (Default and only supported: ./)

    Apart from the workflows, Comet utility can be used to check the current dev and stable versions for the target
    project(s). Example:

    .. code-block:: bash

        $ comet --project-dev-version pcscf icscf

        $ comet --project-stable-version icscf

    For further details, execute the following command from the CLI to print the `help` section for Comet:

    .. code-block:: bash

        $ comet --help

    :return: None
    """
    comet_logger = logging.getLogger()
    # coloredlogs.install(fmt="%(asctime)s %(name)s - %(levelname)s - %(message)s", level='DEBUG')
    coloredlogs.install(fmt="%(levelname)s - %(message)s", level='DEBUG')
    try:
        parser = argparse.ArgumentParser(
            prog="comet")
        logging_group = parser.add_mutually_exclusive_group()
        version_group = parser.add_argument_group(title="Versioning", description="Version related operations")
        flow_group = parser.add_argument_group(title="Workflow", description="Workflows related operations")
        version_group.add_argument(
            "--version",
            action="version",
            help="Print Comet version",
            version="%(prog)s " + __version__
            )
        version_group.add_argument(
            "--projects",
            action="store_true",
            help="Print all the project names"
        )
        version_group.add_argument(
            "--project-dev-version",
            type=str,
            nargs='+',
            help="Print development project version"
        )
        version_group.add_argument(
            "--project-stable-version",
            type=str,
            nargs='+',
            help="Print stable project version"
        )
        logging_group.add_argument(
            "--debug",
            help="Enable debug mode",
            action="store_true"
            )
        logging_group.add_argument(
            "--suppress",
            help="Suppress banner and logging",
            action="store_true"
        )
        flow_group.add_argument(
            "--run",
            choices=[
                "init",
                "branch-flow",
                "release-candidate",
                "release",
                "sync"
            ],
            help="Comet action to execute.\n"
                 "[init: Initialize Comet repository configuration if it does not exist (Interactive mode), "
                 "branch-flow: Upgrade versioning on Git branches for Comet managed project/s, "
                 "release-candidate: Create Release candidate branch for Comet managed project/s], "
                 "release: Release a new version in stable branch for Comet managed project/s], "
                 "sync: Synchronizes the development branch with stable branch"
        )
        flow_group.add_argument(
            "-s",
            "--scm-provider",
            default="bitbucket",
            help="Git SCM provider name"
            )
        flow_group.add_argument(
            "-c",
            "--connection-type",
            default="ssh",
            help="Git SCM provider remote connection type"
            )
        flow_group.add_argument(
            "-u",
            "--username",
            default=None,
            help="Git username"
            )
        flow_group.add_argument(
            "-p",
            "--password",
            default=None,
            help="Git password"
            )
        flow_group.add_argument(
            "-spkp",
            "--ssh-private-key-path",
            default="~/.ssh/id_rsa",
            help="Git SSH local private key path"
            )
        # NOTE: Support for running Comet from any directory is disabled for now
        flow_group.add_argument(
            "-rlp",
            "--repo-local-path",
            default="./",
            choices=[
              "./"
            ],
            help="Git Repository local path (Support for running Comet for "
                 "any path other than './' is disabled for now)"
            )
        flow_group.add_argument(
            "-pc",
            "--project-config",
            default="./.comet.yml",
            help="Git Project configuration file path"
        )
        flow_group.add_argument(
            "--push",
            help="Push changes to remote",
            action="store_true"
        )
        args = parser.parse_args()
        if args.suppress:
            logging.disable(level=logging.CRITICAL)
        elif args.debug:
            banner()
            comet_logger.setLevel(logging.DEBUG)
            comet_logger.info("Comet log level set to debug")
        else:
            banner()
            comet_logger.setLevel(logging.INFO)
        if args.projects:
            project_config = ConfigParser(config_path=args.project_config)
            project_config.read_config()
            print(" ".join(project_config.get_projects()))
        elif args.project_dev_version or args.project_stable_version:
            project_config = ConfigParser(config_path=args.project_config)
            project_config.read_config()
            if args.project_dev_version:
                for project in args.project_dev_version:
                    if project not in [".", "./", ""]:
                        project = os.path.join(os.path.dirname(args.project_config), project)
                    print(f"{project.lstrip('/.')} {project_config.get_project_version(project_path=project, version_type='dev')}")
            if args.project_stable_version:
                for project in args.project_stable_version:
                    if project not in [".", "./", ""]:
                        project = os.path.join(os.path.dirname(args.project_config), project)
                    print(f"{project.lstrip('/.')} {project_config.get_project_version(project_path=project, version_type='stable')}")
        if args.run == "init":
            project_config = ConfigParser(config_path=args.project_config)
            if os.path.exists(args.project_config):
                logging.warning(f"Comet configuration is already initialized at [{args.project_config}]")
                logging.warning(f"Skipping initialization...")
            else:
                logging.info(f"Initializing Comet configuration [{args.project_config}] using interactive mode")
                project_config.initialize_config()
                project_config.write_config()
        elif args.run in ["sync", "branch-flow", "release-candidate", "release"]:
            gitflow = GitFlow(
                scm_provider=args.scm_provider,
                connection_type=args.connection_type,
                username=args.username,
                password=args.password,
                ssh_private_key_path=args.ssh_private_key_path,
                project_local_path=args.repo_local_path,
                project_config_path=args.project_config,
                push_changes=args.push
            )
        if args.run == "branch-flow":
            gitflow.branch_flows()
        elif args.run == "release-candidate":
            gitflow.release_flow(branches=True)
        elif args.run == "release":
            gitflow.release_flow(branches=False)
        elif args.run == "sync":
            gitflow.sync_flow()
    except Exception as err:
        comet_logger.error("Something went wrong! Set --debug flag during execution to view more details")
        comet_logger.error(err)
        sys.exit(1)
    except KeyboardInterrupt:
        comet_logger.error("Interrupted. Exiting...")
        sys.exit(1)


if __name__ == '__main__':
    main()
