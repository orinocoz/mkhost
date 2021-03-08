import logging
import os
import subprocess

##############################################################################
# Common settings
##############################################################################

_version_major   = 0
_version_minor   = 1
_dry_run         = True
_verbose         = False
_non_interactive = False

# Returns the version number as a pair (major, minor)
def get_version():
    return (_version_major, _version_minor)

def get_dry_run():
    return _dry_run

def set_dry_run(b):
    global _dry_run
    _dry_run = bool(b)
    logging.debug("_dry_run: {}".format(_dry_run))

def get_non_interactive():
    return _non_interactive

def set_non_interactive(b):
    global _non_interactive
    _non_interactive = bool(b)
    logging.debug("_non_interactive: {}".format(_non_interactive))

def get_verbose():
    return _verbose

def set_verbose(b):
    global _verbose
    _verbose = bool(b)
    logging.debug("_verbose: {}".format(_verbose))

##############################################################################
# Common functions
##############################################################################

def execute_cmd_interactive(cmdline):
    cmd = " ".join(cmdline)
    logging.info(cmd)
    os.system(cmd)

def execute_cmd(cmdline):
    logging.info(" ".join(cmdline))
    result    = subprocess.run(cmdline, capture_output=True, check=True, encoding='utf-8')
    err_lines = result.stderr.splitlines()
    out_lines = result.stdout.splitlines()
    for x in err_lines:
        logging.warning(x)
    for x in out_lines:
        logging.debug(x)
    return out_lines

# Returns the apt-get command with some default arguments applied.
# A list.
def apt_get_cmd(*args):
    return ["apt-get"]                                          +       \
               (["--dry-run"] if get_dry_run()         else []) +       \
               (["--yes"]     if get_non_interactive() else []) +       \
               list(args)

def update_pkgs():
    execute_cmd_interactive(apt_get_cmd("update"))
    execute_cmd_interactive(apt_get_cmd("upgrade"))

def install_pkgs(pkgs):
    if pkgs:
        execute_cmd_interactive(apt_get_cmd("install", *pkgs))
