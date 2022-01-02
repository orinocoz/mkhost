import logging
import os
import os.path
import pwd
import subprocess

import mkhost.common

# Atomically creates a directory owned by the given uid and gid.
def makedir(path, uid, gid):
    path = os.path.abspath(path)
    logging.info("mkdir {}".format(path))
    os.makedirs(path, mode=0o700, exist_ok=False)
    os.chown(path, uid, gid)

##############################################################################
# System user functions
##############################################################################

def add_system_user(username):
    # TODO: validate username
    try:
        logging.info("add system user: {}".format(username))
        if not mkhost.common.get_dry_run():
            mkhost.common.execute_cmd_batch(['useradd', '--system', '--user-group', '--no-create-home', '--comment', 'mkhost virtual mail owner', username])
    except subprocess.CalledProcessError as e:
        if 9 == e.returncode:
            logging.info("user already exists ({})".format(username))
        else:
            raise

# For the given user name, returns a tuple: (uid, gid).
def get_user_info(username):
    pwinfo = pwd.getpwnam(username)
    return (pwinfo[2], pwinfo[3])
