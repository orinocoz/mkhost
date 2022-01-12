import logging
import os
import os.path
import pwd
import subprocess

import mkhost.cmd
import mkhost.common

# Atomically creates a directory owned by the given uid and gid.
def makedir(path, uid, gid):
    path = os.path.abspath(path)
    logging.info("[unix] mkdir {}".format(path))
    os.makedirs(path, mode=0o700, exist_ok=False)
    os.chown(path, uid, gid)

##############################################################################
# package management functions (apt)
##############################################################################

# Returns the apt-get command with some default arguments applied.
# A list.
def apt_get_cmd(*args):
    return ["apt-get"]                                                        +       \
               (["--dry-run"] if mkhost.common.get_dry_run()         else []) +       \
               (["--yes"]     if mkhost.common.get_non_interactive() else []) +       \
               list(args)

def update_pkgs():
    if not mkhost.common.get_dry_run():
        mkhost.cmd.execute_cmd(apt_get_cmd("update"))
        mkhost.cmd.execute_cmd(apt_get_cmd("upgrade"))

def install_pkgs(pkgs):
    if pkgs:
        mkhost.cmd.execute_cmd(apt_get_cmd("install", *pkgs))

##############################################################################
# user management functions (system)
##############################################################################

def add_system_user(username):
    # TODO: validate username
    try:
        logging.info("[unix] add system user: {}".format(username))
        if not mkhost.common.get_dry_run():
            mkhost.cmd.execute_cmd_batch(['useradd', '--system', '--user-group', '--no-create-home', '--comment', 'mkhost virtual mail owner', username])
    except subprocess.CalledProcessError as e:
        if 9 == e.returncode:
            logging.info("[unix] user already exists ({})".format(username))
        else:
            raise

# For the given user name, returns a tuple: (uid, gid).
def get_user_info(username):
    pwinfo = pwd.getpwnam(username)
    return (pwinfo[2], pwinfo[3])
