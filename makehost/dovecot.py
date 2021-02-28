from makehost.common import install_pkg, execute_cmd

import makehost.dovecot_parser

# Installs and configures Dovecot on the current machine.
#
# Params:
#   doveconf : path to dovecot configuration file
def configure_dovecot(doveconf):
    install_pkg("dovecot-imapd")
    makehost.dovecot_parser.parse_dovecot_config(doveconf)

    # TODO: improve this
    #       -n : Show only settings with non-default values.
    #       Might want to check them all ...
    # execute_cmd(["doveconf", "-nS"])
