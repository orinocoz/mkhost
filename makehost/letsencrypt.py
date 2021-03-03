import makehost.cfg
import makehost.common

# installs Let's Encrypt's certificate
def install():
    makehost.common.install_pkgs(["certbot", "python3-certbot-apache"])
    makehost.common.execute_cmd_interactive(                                                                            \
        ["certbot", "run"] + (["--dry-run"] if makehost.common.get_dry_run() else [])                               +   \
        ["--apache", "--redirect", "--test-cert", "-d", "{}.{}".format(makehost.cfg.MY_HOST_NAME, makehost.cfg.MY_HOST_DOMAIN)])
    # TODO: improve certbot cmdline args

# TODO implement renew/certonly
