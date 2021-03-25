import mkhost.common

# Installs and configures OpenDKIM.
def install():
    mkhost.common.install_pkgs(["opendkim", "opendkim-tools"])
