import logging
import pwd
import subprocess

import mkhost.common

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
