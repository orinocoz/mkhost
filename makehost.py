#!/usr/bin/env python3

import logging
import os
import sys

def execute_cmd(cmd):
    logging.info(cmd)
    os.system(cmd)

if __name__ == "__main__":
    log_format = '[{asctime}] {levelname:8} {message}'
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=log_format, style='{')
    logging.info("Hello from makehost!")
    execute_cmd("ls -la")
