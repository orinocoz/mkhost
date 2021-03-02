from makehost.common import install_pkg, execute_cmd

# Installs and configures Dovecot on the current machine.
#
# Params:
#   doveconf : path to dovecot configuration file
def configure_dovecot(doveconf):
    install_pkg("dovecot-imapd")

    # TODO: improve this
    #       -n : Show only settings with non-default values.
    #       Might want to check them all ...
    # execute_cmd(["doveconf", "-nS"])
