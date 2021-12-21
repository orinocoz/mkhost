#!/usr/bin/env python3

import argparse
import logging
import sys

import mkhost.cfg
import mkhost.common
import mkhost.dovecot
import mkhost.letsencrypt
import mkhost.opendkim
import mkhost.postfix

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Re-configures this machine according to the hardcoded configuration (cfg.py).',
        add_help=True, allow_abbrev=False, epilog="""This program comes with ABSOLUTELY NO WARRANTY.""")

    parser.add_argument("--doveconf",
                        metavar="FILE",
                        required=False,
                        default="/etc/dovecot/dovecot.conf",
                        help="Dovecot configuration file; default: %(default)s")

    parser.add_argument("--letsencrypt",
                        metavar="DIR",
                        required=False,
                        default="/etc/letsencrypt/",
                        help="Let's Encrypt home directory; default: %(default)s")

    parser.add_argument("--batch",
                        required=False,
                        action="store_true",
                        default=False,
                        help="batch mode (non-interactive)")

    parser.add_argument("--dry-run",
                        required=False,
                        action="store_true",
                        default=False,
                        help="dry run (no change)")

    parser.add_argument("--verbose",
                        required=False,
                        action="store_true",
                        default=False,
                        help="verbose processing")

    # Parse command line arguments
    args = parser.parse_args()

    # Setup logging
    log_format = '[{asctime}] {levelname:8} {threadName:<14} {message}'
    logging.basicConfig(stream=sys.stderr, level=(logging.DEBUG if args.verbose else logging.INFO), format=log_format, style='{')

    # Setup global variables
    mkhost.common.set_verbose(args.verbose)
    mkhost.common.set_dry_run(args.dry_run)
    mkhost.common.set_non_interactive(args.batch)

    # validate config
    mkhost.cfg_parser.validate()

    # Destructively re-configure the machine
    logging.info("update system packages...")
    mkhost.common.update_pkgs()
    logging.info("setup letsencrypt...")
    mkhost.letsencrypt.install()
    logging.info("setup opendkim...")
    mkhost.opendkim.install()
    logging.info("setup dovecot...")
    mkhost.dovecot.install(args.doveconf, args.letsencrypt)
    logging.info("setup postfix...")
    mkhost.postfix.install(args.letsencrypt)

    # Print DNS log
    if mkhost.common._dns_log:
        logging.warning("List of DNS changes to apply: {}".format(mkhost.common._dns_log))
    else:
        logging.info("No DNS changes to apply")
