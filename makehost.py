#!/usr/bin/env python3

import logging
import os
import sys

def execute_cmd(cmd):
    logging.info(cmd)
    os.system(cmd)

def install_pkg(pkgname):
    execute_cmd("apt-get install {}".format(pkgname))

if __name__ == "__main__":
    log_format = '[{asctime}] {levelname:8} {message}'
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=log_format, style='{')

    install_pkg("postfix")
    install_pkg("dovecot-imapd")
    install_pkg("mailman3-full")
