import logging
import os
import os.path
import re
import secrets
import shutil
import string
import tempfile

import mkhost.common
import mkhost.cfg
import mkhost.cfg_parser
import mkhost.letsencrypt
import mkhost.unix

re_users = re.compile(
    '^([^:]+):\{([-\w]+)\}\$(\w+)\$[^:]*:(\d*):(\d*)::::$', re.ASCII)

pwd_hash_cmd = ["doveadm", "pw", "-s", "SHA512-CRYPT"]

# generate a new password
def gen_pwd():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(18))

# generate a new user password
def gen_pwd_hash(username):
    # TODO check what password schemes are available: doveadm pw -l
    if mkhost.common.get_non_interactive():
        pwd = gen_pwd()
        logging.info("New password for {}: {}".format(username, pwd))
        return mkhost.cmd.execute_cmd_batch(pwd_hash_cmd, input=(pwd + os.linesep + pwd + os.linesep))[0][0]
        # TODO clear error message if number of output lines != 1
    else:
        logging.info("New password for {}".format(username))
        return mkhost.cmd.execute_cmd_interactive(pwd_hash_cmd)[0][0]
        # TODO clear error message if number of output lines != 1

# Generates Dovecot configuration and writes it to the given configuration file
# (which must be the main Dovecot configuration file).
#
# Params:
#   doveconf         : path to the main Dovecot configuration file
#   letsencrypt_home : Let's Encrypt home dir
def write_config(doveconf, letsencrypt_home):
    with open(doveconf) as f:
        for line in f:
            m = mkhost.common.re_mkhost_header.match(line)
            if m:
                mver = (int(m.group(1)), int(m.group(2)))
                logging.info("Found mkhost {}.{} dovecot configuration header".format(mver[0], mver[1]))
                if (mkhost.common.get_version() <= mver):
                    return

    configuration = """
########################################################################
{}
########################################################################

# Kill all clients when Dovecot master process shuts down.
shutdown_clients = yes

# Disable cleartext authentication unless SSL/TLS is used
# or the connection is local.
disable_plaintext_auth = yes

# Just plain authentication using a password.
# Login mechanism is for Outlook client.
auth_mechanisms = plain login

# Allow full filesystem access to clients?
mail_full_filesystem_access = no

# Verbose logging so that we know what is going on.
auth_verbose      = yes
verbose_ssl       = yes
verbose_proctitle = yes

protocols    = {}
""".format(mkhost.common.mkhost_header(),
           " ".join(mkhost.cfg.DOVECOT_PROTOCOLS))

    # Listen on the loopback address only
    if mkhost.cfg.DOVECOT_LOOPBACK_ONLY:
        logging.info("Dovecot will listen on IPv4 and IPv6 loopback addresses only")
        configuration += """
listen = 127.0.0.1, ::1
"""
    else:
        logging.info("Dovecot will listen on all available interfaces")

    configuration += """
########################################################################
# Authentication for system users
########################################################################

passdb {{
  driver          = pam
  args            = dovecot
  override_fields = allow_nets=127.0.0.1/32
}}

userdb {{
  driver          = passwd
  override_fields = mail=maildir:{}
}}
""".format(os.path.join(mkhost.cfg.LOCAL_MAILBOX_BASE, '%u/'))

    configuration += """
########################################################################
# Authentication for passwd-file users.
#
# Virtual user credentials are in {} .
########################################################################

passdb {{
  driver = passwd-file
  args   = scheme=SHA512-CRYPT username_format=%u {}
}}

userdb {{
  driver = passwd-file
  args   = username_format=%u {}

  # Default fields that can be overridden by passwd-file
  default_fields  = uid={} gid={} home={} quota_rule=*:storage=1M

  # Override fields from passwd-file
  override_fields = home={}
}}
""".format(mkhost.cfg.DOVECOT_USERS_DB,
           mkhost.cfg.DOVECOT_USERS_DB,
           mkhost.cfg.DOVECOT_USERS_DB,
           mkhost.cfg.VIRTUAL_MAIL_USER,
           mkhost.cfg.VIRTUAL_MAIL_USER,
           os.path.join(mkhost.cfg.VIRTUAL_MAILBOX_BASE, '%d/%n/'),
           os.path.join(mkhost.cfg.VIRTUAL_MAILBOX_BASE, '%d/%n/'))

    configuration += """
########################################################################
# Mail layout
########################################################################

mail_home     = {}
mail_location = maildir:~/mail/
""".format(os.path.join(mkhost.cfg.VIRTUAL_MAILBOX_BASE, '%d/%n/'))

    configuration += """
namespace inbox {
  type  = private
  inbox = yes

  mailbox Drafts {
    auto        = create
    special_use = \Drafts
  }
  mailbox Junk {
    auto        = create
    special_use = \Junk
  }
  mailbox Sent {
    auto        = subscribe
    special_use = \Sent
  }
  mailbox Trash {
    auto        = create
    special_use = \Trash
  }
  mailbox virtual/All {
    auto        = no
    special_use = \All
  }
}

########################################################################
# User authentication service for Postfix
########################################################################

service auth {
  unix_listener /var/spool/postfix/private/auth {
    group = postfix
    mode  = 0660
    user  = postfix
  }
}
"""

    configuration += """
########################################################################
# SSL settings
########################################################################

ssl      = required
ssl_cert = <{}
ssl_key  = <{}
""".format(mkhost.letsencrypt.cert_path(letsencrypt_home),
           mkhost.letsencrypt.key_path(letsencrypt_home))

    # overwrite the configuration file
    if not mkhost.common.get_dry_run():
        logging.info("writing configuration to {}".format(doveconf))
        with open(doveconf, "a") as f:
            print(configuration, file=f)

    logging.debug(configuration)

# Generates and writes out user database file (mkhost.cfg.DOVECOT_USERS_DB).
def write_users_db():
    vboxes = mkhost.cfg_parser.get_virtual_mailboxes()

    # Parse the existing user db file, filter users
    old_lines = []
    try:
        with open(mkhost.cfg.DOVECOT_USERS_DB) as f:
            for line in map(lambda x: x.rstrip(), f):
                if mkhost.common.re_comment.match(line):
                    old_lines.append(line)
                elif mkhost.common.re_blank.match(line):
                    old_lines.append(line)
                else:
                    m = re_users.match(line)

                    if m:
                        username = m.group(1)

                        if username in vboxes:
                            logging.info("[dovecot] user already exists: {}".format(username))
                            old_lines.append(line)
                            vboxes.remove(username)
                        else:
                            logging.info("[dovecot] delete user: {}".format(username))
                    else:
                        logging.warning("{}: invalid line: {}".format(mkhost.cfg.DOVECOT_USERS_DB, line))
    except FileNotFoundError:
        logging.warning("dovecot user db file does not exist: {}".format(mkhost.cfg.DOVECOT_USERS_DB))

    # create new user db file
    with tempfile.NamedTemporaryFile(mode="wt", prefix="mkhost-", delete=True) as f:
        logging.debug("temp file: {}".format(f.name))
        if old_lines:
            print(os.linesep.join(old_lines), file=f)
        if vboxes:
            print(mkhost.common.mkhost_header(), file=f)
            for x in vboxes:
                logging.info("create user: {}".format(x))
                print("{}:{}::::::".format(x,gen_pwd_hash(x)), file=f)

        # overwrite old user db file
        if not mkhost.common.get_dry_run():
            f.flush()
            shutil.copyfile(f.name, mkhost.cfg.DOVECOT_USERS_DB)

# Installs and configures Dovecot.
#
# Params:
#   doveconf         : path to dovecot configuration file
#   letsencrypt_home : Let's Encrypt home dir
def install(doveconf, letsencrypt_home):
    mkhost.unix.install_pkgs(["dovecot-imapd"])

    write_config(doveconf, letsencrypt_home)
    write_users_db()
