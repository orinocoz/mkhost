import mkhost.cfg
import mkhost.common

# Installs Let's Encrypt's certificate.
def install():
    mkhost.common.install_pkgs(["certbot", "python3-certbot-apache"])
    mkhost.common.execute_cmd(
        ["certbot", "run"] +
        (["--dry-run"] if mkhost.common.get_dry_run() else [])          +   \
        (["-n"] if mkhost.common.get_non_interactive() else [])         +   \
        ["--apache", "--redirect", "--test-cert", "-d", "{}.{}".format(mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN)])
    # TODO: improve certbot cmdline args

# TODO implement renew/certonly
