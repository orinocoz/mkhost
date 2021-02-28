from makehost.common import install_pkg, execute_cmd

import makehost.dovecot_parser

def configure_dovecot():
    install_pkg("dovecot-imapd")
    # TODO: improve this
    #       -n : Show only settings with non-default values.
    #       Might want to check them all ...
    execute_cmd(["doveconf", "-nS"])
