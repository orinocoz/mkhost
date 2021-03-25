import logging
import os.path
import shutil
import tempfile

import mkhost.cfg
import mkhost.cfg_parser
import mkhost.common

def gen_selector():
    # TODO: make this time based
    return "mkhost"

def genkey(domain):
    selector = gen_selector()
    logging.info("opendkim-genkey: {}; selector: {}".format(domain, selector))

    if not mkhost.common.get_dry_run():
        domain_dir = os.path.join(mkhost.cfg.OPENDKIM_KEYS, domain)
        os.makedirs(domain_dir, mode=0o755, exist_ok=True)

    try:
        tempdir = tempfile.mkdtemp(prefix="mkhost-")
        logging.debug("tempdir: {}".format(tempdir))
        mkhost.common.execute_cmd([
            "opendkim-genkey", "-a", "-r", "-d", domain, "-s", selector, "-D", tempdir])

        if not mkhost.common.get_dry_run():
            shutil.move(os.path.join(tempdir, "{}.txt".format(selector)), domain_dir)
            shutil.move(os.path.join(tempdir, "{}.private".format(selector)), domain_dir)
            # TODO: check for file overwrite
    except:
        shutil.rmtree(tempdir, ignore_errors=True)
        raise

# Installs and configures OpenDKIM.
def install():
    mkhost.common.install_pkgs(["opendkim", "opendkim-tools"])

    domains = mkhost.cfg_parser.get_alias_domains()
    logging.debug("alias_domains: {}".format(domains))
    for d in domains:
        genkey(d)

    domains = mkhost.cfg_parser.get_mailbox_domains()
    logging.debug("mailbox_domains: {}".format(domains))
    for d in domains:
        genkey(d)
