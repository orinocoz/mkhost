#!/usr/bin/env python3

import logging
import os
import sys

def execute_cmd(cmd):
    logging.info(cmd)
    os.system(cmd)

def install_pkg(pkgname):
    execute_cmd("apt-get install {}".format(pkgname))

def install_dovecot():
    install_pkg("dovecot-imapd")

def install_postfix():
    install_pkg("postfix")

# def install_mailman3():
#     install_pkg("mailman3-full")

if __name__ == "__main__":
    log_format = '[{asctime}] {levelname:8} {message}'
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=log_format, style='{')

    install_dovecot()
    install_postfix()
    # install_mailman3()
