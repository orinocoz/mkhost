import copy
import logging
import os.path
import pathlib
import re
import shutil
import tempfile

import mkhost.cfg
import mkhost.cfg_parser
import mkhost.common

re_key_value = re.compile(
    '^(\w+)\s+(\S+)\s*$', re.ASCII)

OPENDKIM_CONFIG = {
    "AllowSHA1Only"    : False,
    "KeyTable"         : mkhost.cfg.OPENDKIM_KEYTABLE,
    "LogResults"       : True,
    "LogWhy"           : True,
    "Mode"             : "sv",
    "RequireSafeKeys"  : True,
    "SyslogSuccess"    : True,
}

def gen_selector():
    return mkhost.common.get_run_ts().strftime("%Y%m%d%H%M%S")

# Generates and writes out OpenDKIM keytable file (mkhost.cfg.OPENDKIM_KEYTABLE).
def write_keytable():
    selector = gen_selector()
    domains  = mkhost.cfg_parser.get_mailbox_domains()

    # create new config file
    with tempfile.NamedTemporaryFile(mode="wt", prefix="mkhost-", delete=True) as f:
        logging.debug("temp file: {}".format(f.name))
        for d in domains:
            logging.info("opendkim keytable: {}".format(d))
            pk_path  = os.path.join(mkhost.cfg.OPENDKIM_KEYS, d, "{}.private".format(selector))     # private key file
            key_name = d                                                                            # key name is just the domain name
            print("{}        {}:{}:{}".format(key_name, d, selector, pk_path), file=f)
            # TODO: fix column alignment; check the length of the longest domain

        # overwrite the old config file
        if not mkhost.common.get_dry_run():
            f.flush()
            logging.info("write opendkim keytable to {}".format(mkhost.cfg.OPENDKIM_KEYTABLE))
            shutil.copyfile(f.name, mkhost.cfg.OPENDKIM_KEYTABLE)

# Generates and writes out OpenDKIM config file (mkhost.cfg.OPENDKIM_CONF).
def write_conf():
    new_cfg   = copy.deepcopy(OPENDKIM_CONFIG)
    old_lines = []

    try:
        # Parse the existing configuration file
        with open(mkhost.cfg.OPENDKIM_CONF) as f:
            for line in map(lambda x: x.rstrip(), f):
                if mkhost.common.re_comment.match(line):
                    old_lines.append(line)
                elif mkhost.common.re_blank.match(line):
                    old_lines.append(line)
                else:
                    m = re_key_value.match(line)

                    if m:
                        key = m.group(1)
                        val = m.group(2)

                        # logging.debug("opendkim: {} => {}".format(key,val))
                        if (key not in OPENDKIM_CONFIG) or (str(OPENDKIM_CONFIG[key]) == val):
                            logging.debug("opendkim save: {} => {}".format(key,val))
                            old_lines.append(line)
                            new_cfg.pop(key,None)
                        else:
                            logging.debug("opendkim drop: {} => {}".format(key,val))
                    else:
                        logging.warning("{}: invalid line: {}".format(mkhost.cfg.OPENDKIM_CONF, line))
    except FileNotFoundError:
        logging.warning("OpenDKIM config file does not exist: {}".format(mkhost.cfg.OPENDKIM_CONF))

    # create new config file
    with tempfile.NamedTemporaryFile(mode="wt", prefix="mkhost-", delete=True) as f:
        logging.debug("temp file: {}".format(f.name))
        if old_lines:
            print(os.linesep.join(old_lines), file=f)
        if new_cfg:
            print(mkhost.common.mkhost_header(), file=f)
            for x,y in new_cfg.items():
                logging.info("opendkim  new: {} => {}".format(x,y))
                print("{:<24} {}".format(x,y), file=f)

        # overwrite the old config file
        if not mkhost.common.get_dry_run():
            f.flush()
            logging.info("write opendkim config to {}".format(mkhost.cfg.OPENDKIM_CONF))
            shutil.copyfile(f.name, mkhost.cfg.OPENDKIM_CONF)

# Given a domain name, generates a selector, a public-private key pair
# and writes them to a file.
def genkey(domain):
    selector = gen_selector()
    logging.info("opendkim-genkey selector: {}; domain: {}".format(selector, domain))

    if not mkhost.common.get_dry_run():
        domain_dir = os.path.join(mkhost.cfg.OPENDKIM_KEYS, domain)
        os.makedirs(domain_dir, mode=0o755, exist_ok=True)

    try:
        tempdir = tempfile.mkdtemp(prefix="mkhost-")
        logging.debug("tempdir: {}".format(tempdir))
        mkhost.common.execute_cmd([
            "opendkim-genkey", "-a", "-r", "-d", domain, "-s", selector, "-D", tempdir])

        if not mkhost.common.get_dry_run():
            dns_rec_file = os.path.join(tempdir, "{}.txt".format(selector))
            mkhost.common.add_dns_record(pathlib.Path(dns_rec_file).read_text())
            shutil.move(dns_rec_file, domain_dir)
            shutil.move(os.path.join(tempdir, "{}.private".format(selector)), domain_dir)
    except shutil.Error as e:
        shutil.rmtree(tempdir, ignore_errors=True)
        logging.warning("Error installing new OpenDKIM keys for {}, skipping: {}".format(domain, e))
    except Exception as e:
        shutil.rmtree(tempdir, ignore_errors=True)
        raise

# Installs and configures OpenDKIM.
def install():
    mkhost.common.install_pkgs(["opendkim", "opendkim-tools"])

    domains = mkhost.cfg_parser.get_alias_domains()
    logging.info("alias_domains: {}".format(domains))
    for d in domains:
        genkey(d)

    domains = mkhost.cfg_parser.get_mailbox_domains()
    logging.info("mailbox_domains: {}".format(domains))
    for d in domains:
        genkey(d)

    write_keytable()
    write_conf()
