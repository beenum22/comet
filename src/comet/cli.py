#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Muneeb Ahmad'
__version__ = '0.1.0'

import sys
import argparse
from .work_flows import GitFlow
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
Comet is a simple tool to automate/facilitate automated release cycle.

Copyright 2021 Muneeb Ahmad
{Style.RESET_ALL}""")


def main():
    # formatter = "%(asctime)s %(name)s - %(levelname)s - %(message)s"
    comet_logger = logging.getLogger()
    # coloredlogs.install(fmt="%(asctime)s %(name)s - %(levelname)s - %(message)s", level='DEBUG')
    coloredlogs.install(fmt="%(levelname)s - %(message)s", level='DEBUG')
    banner()
    try:
        usage = ('python %prog <add variables here>')
        parser = argparse.ArgumentParser(
            prog="comet",
            description="WIP")
        parser.add_argument(
            "--version",
            action="version",
            help="Print Comet version",
            version="%(prog)s " + __version__
            )
        parser.add_argument(
            "--debug",
            help="Debug mode.",
            action="store_true"
            )
        parser.add_argument(
            "-s",
            "--scm_provider",
            default="bitbucket",
            help="Git SCM provider name"
            )
        parser.add_argument(
            "-c",
            "--connection_type",
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
        parser.add_argument(
            "-rlp",
            "--repo-local-path",
            default="./",
            help="Git Repository local path"
            )
        parser.add_argument(
            "-pc",
            "--project-config",
            default="./.comet.yml",
            help="Git Project configuration file path"
        )
        parser.add_argument(
            "--workflow",
            required=True,
            choices=[
                "development"
            ],
            help="Work flow to execute"
        )
        args = parser.parse_args()
        if args.debug:
            comet_logger.setLevel(logging.DEBUG)
            comet_logger.info("Comet log level set to debug")
        else:
            comet_logger.setLevel(logging.INFO)
        # c = ConfigParser(config_path=".test_comet.yml")
        # c.initialize_config()
        gitflow = GitFlow(
            scm_provider=args.scm_provider,
            connection_type=args.connection_type,
            username=args.username,
            password=args.password,
            ssh_private_key_path=args.ssh_private_key_path,
            project_local_path=args.repo_local_path,
            project_config_path=args.project_config
        )
        if gitflow.scm.source_branch == gitflow.project_config.config["development_branch"]:
            gitflow.development_flow()
        elif gitflow.scm.source_branch == gitflow.project_config.config["stable_branch"]:
            gitflow.stable_flow()
        else:
            logging.warning(f"No work flow is implemented for the branch [{gitflow.scm.source_branch}]")
    except Exception as err:
        comet_logger.error("Something went wrong! Set --debug flag during execution to view more details")
        comet_logger.error(err)
    except KeyboardInterrupt:
        comet_logger.error("Interrupted. Exiting...")
        sys.exit()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
