#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Muneeb Ahmad'
__version__ = '0.1.0'

import sys
import os
import argparse
from .work_flows import GitFlow
from .config import ConfigParser
import logging.config
from colorama import Fore, Style
import coloredlogs


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

Copyright 2021 Muneeb Ahmad
{Style.RESET_ALL}""")


def main():
    comet_logger = logging.getLogger()
    # coloredlogs.install(fmt="%(asctime)s %(name)s - %(levelname)s - %(message)s", level='DEBUG')
    coloredlogs.install(fmt="%(levelname)s - %(message)s", level='DEBUG')
    try:
        parser = argparse.ArgumentParser(
            prog="comet",
            description=banner())
        parser.add_argument(
            "--version",
            action="version",
            help="Print Comet version",
            version="%(prog)s " + __version__
            )
        parser.add_argument(
            "--project-version",
            action="store_true",
            help="Print project version"
        )
        parser.add_argument(
            "--debug",
            help="Debug mode.",
            action="store_true"
            )
        parser.add_argument(
            "-s",
            "--scm-provider",
            default="bitbucket",
            help="Git SCM provider name"
            )
        parser.add_argument(
            "-c",
            "--connection-type",
            default="ssh",
            help="Git SCM provider remote connection type"
            )
        parser.add_argument(
            "-u",
            "--username",
            default=None,
            help="Git username"
            )
        parser.add_argument(
            "-p",
            "--password",
            default=None,
            help="Git password"
            )
        parser.add_argument(
            "-spkp",
            "--ssh-private-key-path",
            default="~/.ssh/id_rsa",
            help="Git SSH local private key path"
            )
        # NOTE: Support for running Comet from any directory is disabled for now
        parser.add_argument(
            "-rlp",
            "--repo-local-path",
            default="./",
            choices=[
              "./"
            ],
            help="Git Repository local path (Support for running Comet for "
                 "any path other than './' is disabled for now)"
            )
        parser.add_argument(
            "-pc",
            "--project-config",
            default="./.comet.yml",
            help="Git Project configuration file path"
        )
        parser.add_argument(
            "--run",
            choices=[
                "init",
                "branch-flow",
                "release-candidate",
                "release"
            ],
            help="Comet action to execute.\n"
                 "[init: Initialize Comet repository configuration if it doesn't exist (Interactive mode), "
                 "branch-flow: Upgrade versioning on Git branches for Comet managed project/s,"
                 "release-flow: Create Release branches for Comet managed project/s]"
        )
        args = parser.parse_args()
        if args.debug:
            comet_logger.setLevel(logging.DEBUG)
            comet_logger.info("Comet log level set to debug")
        else:
            comet_logger.setLevel(logging.INFO)
        if args.project_version:
            project_config = ConfigParser(config_path=args.project_config)
            project_config.read_config()
            print(f"Project Versions:")
            for project in project_config.config["projects"]:
                print(f"  Sub-project: {project['path']}\n"
                      f"    Development Version: {project_config.get_project_version(project_path=project['path'], version_type='dev')}\n"
                      f"    Stable Version: {project_config.get_project_version(project_path=project['path'], version_type='stable')}"
                )
        if args.run == "init":
            project_config = ConfigParser(config_path=args.project_config)
            if os.path.exists(args.project_config):
                logging.warning(f"Comet configuration is already initialized at [{args.project_config}]")
                logging.warning(f"Skipping initialization...")
            else:
                logging.info(f"Initializing Comet configuration [{args.project_config}] using interactive mode")
                project_config.initialize_config()
                project_config.write_config()
        elif args.run in ["branch-flow", "release-candidate", "release"]:
            gitflow = GitFlow(
                scm_provider=args.scm_provider,
                connection_type=args.connection_type,
                username=args.username,
                password=args.password,
                ssh_private_key_path=args.ssh_private_key_path,
                project_local_path=args.repo_local_path,
                project_config_path=args.project_config
            )
        if args.run == "branch-flow":
            gitflow.branch_flows()
        elif args.run == "release-candidate":
            gitflow.release_flow(branches=True)
        elif args.run == "release":
            gitflow.release_flow(branches=False)
    except Exception as err:
        comet_logger.error("Something went wrong! Set --debug flag during execution to view more details")
        comet_logger.error(err)
        sys.exit(1)
    except KeyboardInterrupt:
        comet_logger.error("Interrupted. Exiting...")
        sys.exit(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
