import os.path

import mkhost.cfg
import mkhost.common

def cert_path(letsencrypt_home):
    return os.path.join(
        letsencrypt_home, "live", "{}.{}".format(mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN), "cert.pem")

def key_path(letsencrypt_home):
    return os.path.join(
        letsencrypt_home, "live", "{}.{}".format(mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN), "privkey.pem")

# Installs Let's Encrypt's certificate.
def install():
    mkhost.common.install_pkgs(["certbot", "python3-certbot-apache"])
    mkhost.common.execute_cmd(
        ["certbot"] + \
        (["certonly", "--dry-run"] if mkhost.common.get_dry_run() else ["run"]) + \
        (["--non-interactive", "--agree-tos"] if mkhost.common.get_non_interactive() else []) + \
        ["--email", "{}".format(mkhost.cfg.X509_EMAIL)] + \
        ["--apache", "--redirect", "--domain", "{}.{}".format(mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN)])

# TODO implement renew/certonly
