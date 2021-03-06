import datetime
import logging
import re

import mkhost.common
import mkhost.cfg

re_mkhost_header = re.compile('^# mkhost config created at [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}\+[0-9]{2}:[0-9]{2}$', re.ASCII)

# Installs and configures Dovecot.
#
# Params:
#   doveconf : path to dovecot configuration file
def install(doveconf):
    mkhost.common.install_pkgs(["dovecot-imapd"])

    with open(doveconf) as f:
        for line in f:
            if re_mkhost_header.match(line):
                logging.debug("mkhost dovecot configuration header line already exists: {}".format(line))
                return

    # append new configuration to the main config file
    ts = datetime.datetime.now(datetime.timezone.utc)

    configuration = """
########################################################################
# mkhost config created at {}
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
""".format(ts.isoformat(), " ".join(mkhost.cfg.DOVECOT_PROTOCOLS))

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

########################################################################
# Authentication for passwd-file users.
#
# Virtual user credentials are in /etc/dovecot/users .
########################################################################

passdb {{
  driver = passwd-file
  args   = scheme=SHA512-CRYPT username_format=%u /etc/dovecot/users
}}

userdb {{
  driver = passwd-file
  args   = username_format=%u /etc/dovecot/users

  # Default fields that can be overridden by passwd-file
  default_fields  = uid=mailv gid=mailv home=/var/mailv/%d/%n/ quota_rule=*:storage=1M

  # Override fields from passwd-file
  override_fields = home=/var/mailv/%d/%n/
}}

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

########################################################################
# SSL settings
########################################################################

ssl      = required
ssl_cert = </etc/letsencrypt/live/{}.{}/cert.pem
ssl_key  = </etc/letsencrypt/live/{}.{}/privkey.pem
""".format(mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN, mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN)

    logging.info("writing configuration to {}".format(doveconf))
    with open(doveconf, "a") as f:
        if not mkhost.common.get_dry_run():
            print(configuration, file=f)
    logging.debug(configuration)
