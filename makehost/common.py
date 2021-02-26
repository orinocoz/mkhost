import logging
import os
import subprocess

##############################################################################
# Common settings
##############################################################################

dry_run         = True
verbose         = False
non_interactive = False

def set_dry_run(b):
    global dry_run
    dry_run = bool(b)

def set_non_interactive(b):
    global non_interactive
    non_interactive = bool(b)

def set_verbose(b):
    global verbose
    verbose = bool(b)

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
    return ["apt-get"]                                    +       \
               (["--dry-run"] if dry_run         else []) +       \
               (["--yes"]     if non_interactive else []) +       \
               list(args)

def update_pkgs():
    execute_cmd_interactive(apt_get_cmd("update"))
    execute_cmd_interactive(apt_get_cmd("upgrade"))

def install_pkg(pkgname):
    execute_cmd_interactive(apt_get_cmd("install", pkgname))
