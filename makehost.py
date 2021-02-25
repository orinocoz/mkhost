#!/usr/bin/env python3

import logging
import os
import sys

import cfg

def execute_cmd(cmd):
    logging.info(cmd)
    os.system(cmd)

def update_pkgs():
    execute_cmd("apt-get update")
    execute_cmd("apt-get upgrade")

def install_pkg(pkgname):
    execute_cmd("apt-get install {}".format(pkgname))

def configure_dovecot():
    install_pkg("dovecot-imapd")

def install_postfix():
    install_pkg("postfix")

if __name__ == "__main__":
    log_format = '[{asctime}] {levelname:8} {message}'
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=log_format, style='{')

    update_pkgs()
    configure_dovecot()
    install_postfix()
