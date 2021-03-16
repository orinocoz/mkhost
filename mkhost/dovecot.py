import datetime
import logging
import os
import re
import shutil
import tempfile

import mkhost.common
import mkhost.cfg
import mkhost.cfg_parser

re_mkhost_blank = re.compile(
    '^\s*$', re.ASCII)
re_mkhost_comment = re.compile(
    '^\s*#.*$', re.ASCII)
re_mkhost_header = re.compile(
    '^# mkhost ([0-9]+)\.([0-9]+) config created at [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}\+[0-9]{2}:[0-9]{2}$', re.ASCII)
re_mkhost_users = re.compile(
    '^([^:]+):\{([-\w]+)\}\$(\w+)\$[^:]*:(\d*):(\d*)::::$', re.ASCII)

# Generates Dovecot configuration and writes it to the given configuration file
# (which must be the main Dovecot configuration file).
#
# Params:
#   doveconf : path to the main Dovecot configuration file
def write_config(doveconf):
    with open(doveconf) as f:
        for line in f:
            m = re_mkhost_header.match(line)
            if m:
                mver = (int(m.group(1)), int(m.group(2)))
                logging.info("Found mkhost {}.{} dovecot configuration header".format(mver[0], mver[1]))
                if (mkhost.common.get_version() <= mver):
                    return

    # append new configuration to the main config file
    ts = datetime.datetime.now(datetime.timezone.utc)

    configuration = """
########################################################################
# mkhost {}.{} config created at {}
########################################################################

# Kill all clients when Dovecot master process shuts down.
shutdown_clients = yes

# Disable cleartext authentication unless SSL/TLS is used
# or the connection is local.
disable_plaintext_auth = yes

# Just plain authentication using a password.
auth_mechanisms = plain

# Allow full filesystem access to clients?
mail_full_filesystem_access = no

# Verbose logging so that we know what is going on.
auth_verbose = yes
verbose_ssl  = yes

protocols    = {}
""".format(mkhost.common._version_major,
           mkhost.common._version_minor,
           ts.isoformat(),
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
  override_fields = mail=maildir:/var/mail/%u/
}}
"""

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
  default_fields  = uid=mailv gid=mailv home=/var/mailv/%d/%n/ quota_rule=*:storage=1M

  # Override fields from passwd-file
  override_fields = home=/var/mailv/%d/%n/
}}
""".format(mkhost.cfg.DOVECOT_USERS_DB,
           mkhost.cfg.DOVECOT_USERS_DB,
           mkhost.cfg.DOVECOT_USERS_DB)

    configuration += """
########################################################################
# Mail layout
########################################################################

mail_home     = /var/mailv/%d/%n/
mail_location = maildir:~/mail/

namespace inbox {{
  type  = private
  inbox = yes

  mailbox Drafts {{
    auto        = create
    special_use = \Drafts
  }}
  mailbox Junk {{
    auto        = create
    special_use = \Junk
  }}
  mailbox Sent {{
    auto        = subscribe
    special_use = \Sent
  }}
  mailbox Trash {{
    auto        = create
    special_use = \Trash
  }}
  mailbox virtual/All {{
    auto        = no
    special_use = \All
  }}
}}

########################################################################
# User authentication service for Postfix
########################################################################

service auth {{
  unix_listener /var/spool/postfix/private/auth {{
    group = postfix
    mode  = 0660
    user  = postfix
  }}
}}
"""

    configuration += """
########################################################################
# SSL settings
########################################################################

ssl      = required
ssl_cert = </etc/letsencrypt/live/{}.{}/cert.pem
ssl_key  = </etc/letsencrypt/live/{}.{}/privkey.pem
""".format(mkhost.cfg.MY_HOST_NAME,
           mkhost.cfg.MY_HOST_DOMAIN,
           mkhost.cfg.MY_HOST_NAME,
           mkhost.cfg.MY_HOST_DOMAIN)

    # overwrite the configuration file
    if not mkhost.common.get_dry_run():
        logging.info("writing configuration to {}".format(doveconf))
        with open(doveconf, "a") as f:
            print(configuration, file=f)

    logging.debug(configuration)

def write_users_db():
    vboxes = mkhost.cfg_parser.get_virtual_mailboxes()
    logging.debug("vboxes : {}".format(vboxes))

    # Parse the existing user db file, filter users
    old_users = []
    try:
        with open(mkhost.cfg.DOVECOT_USERS_DB) as f:
            for line in f:
                if (not re_mkhost_comment.match(line)) and (not re_mkhost_blank.match(line)):
                    m = re_mkhost_users.match(line)

                    if m:
                        username = m.group(1)

                        if username in vboxes:
                            logging.debug("user already exists: {}".format(username))
                            old_users.append(line)
                            vboxes.remove(username)
                        else:
                            logging.debug("delete user: {}".format(username))
                    else:
                        logging.warning("{}: invalid line: {}".format(mkhost.cfg.DOVECOT_USERS_DB, line))
    except FileNotFoundError:
        logging.warning("dovecot user db file does not exist: {}".format(mkhost.cfg.DOVECOT_USERS_DB))

    # create new user db file
    with tempfile.NamedTemporaryFile(mode="wt", prefix="mkhost-", delete=True) as f:
        logging.debug("temp file: {}".format(f.name))
        print('Hello world! this is mkhost ...', file=f)
        print(os.linesep.join(old_users), file=f)
        for x in vboxes:
            logging.debug("vbox: {}".format(x))
            print("vbox: {}".format(x), file=f)
        f.flush()

        # overwrite old user db file
        if not mkhost.common.get_dry_run():
            shutil.copyfile(f.name, mkhost.cfg.DOVECOT_USERS_DB)

# Installs and configures Dovecot.
#
# Params:
#   doveconf : path to dovecot configuration file
def install(doveconf):
    mkhost.common.install_pkgs(["dovecot-imapd"])

    write_config(doveconf)
    write_users_db()
