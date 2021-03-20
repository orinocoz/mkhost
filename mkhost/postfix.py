import mkhost.common

# Installs and configures Postfix.
def install():
    mkhost.common.install_pkgs(["postfix"])
