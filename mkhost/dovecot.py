import datetime
import logging
import re

import mkhost.common

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

auth_verbose = yes
default_client_limit = 100
default_process_limit = 10
mail_home = /var/mailv/%d/%n/
mail_location = maildir:~/mail/
namespace inbox {{
  inbox = yes
  location =
  mailbox Drafts {{
    auto = create
    special_use = \Drafts
  }}
}}
""".format(ts.isoformat())

    logging.info("writing configuration to {}".format(doveconf))
    with open(doveconf, "a") as f:
        if not mkhost.common.get_dry_run():
            print(configuration, file=f)
    logging.debug(configuration)
