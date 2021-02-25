#!/usr/bin/env python3

import argparse
import logging
import os
import sys

import makehost.cfg

def execute_cmd_interactive(cmdline):
    cmd = " ".join(cmdline)
    logging.info(cmd)
    os.system(cmd)

# Returns the apt-get command with some default arguments applied.
# A list.
def apt_get_cmd(*args):
    return ["apt-get"]                                          +       \
               (["--dry-run"] if makehost_args.dry_run else []) +       \
               (["--yes"]     if makehost_args.batch   else []) +       \
               list(args)

def update_pkgs():
    execute_cmd_interactive(apt_get_cmd("update"))
    execute_cmd_interactive(apt_get_cmd("upgrade"))

def install_pkg(pkgname):
    execute_cmd_interactive(apt_get_cmd("install", pkgname))

def configure_dovecot():
    install_pkg("dovecot-imapd")

def install_postfix():
    install_pkg("postfix")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Re-configures this machine according to the configuration.',
        add_help=True, allow_abbrev=False, epilog="""This program comes with ABSOLUTELY NO WARRANTY.""")

    parser.add_argument("--batch",
                        required=False,
                        action="store_true",
                        help="batch mode (non-interactive)")

    parser.add_argument("--dry-run",
                        required=False,
                        action="store_true",
                        help="dry run (no change)")

    parser.add_argument("--verbose",
                        required=False,
                        action="store_true",
                        help="verbose processing")

    # Parse command line arguments
    makehost_args = parser.parse_args()

    # Setup logging
    log_format = '[{asctime}] {levelname:8} {message}'
    logging.basicConfig(stream=sys.stderr, level=(logging.DEBUG if makehost_args.verbose else logging.INFO), format=log_format, style='{')

    # Destructively re-configure the machine
    update_pkgs()
    configure_dovecot()
    install_postfix()
