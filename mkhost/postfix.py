import copy
import logging
import os
import re
import shutil
import tempfile

import mkhost.cfg
import mkhost.common
import mkhost.letsencrypt

re_valias    = re.compile(
    '^([^@]+)@([^@]+?)\s+(\S+@\S+)((?:\s*,\s*\S+@\S+)*)$', re.ASCII)
re_vmailbox  = re.compile(
    '^([^@]+)@([^@]+?)\s+(\S+)$', re.ASCII)

def postconf_del(key):
    mkhost.common.execute_cmd(["postconf", "-v", "-#", "{}".format(key)])

def postconf_get(key):
    return mkhost.common.execute_cmd(["postconf", "-h", "{}".format(key)])[0][0]

def postconf_set(key, value):
    mkhost.common.execute_cmd(["postconf", "-v", "-e", "{}={}".format(key,value)])

def postconf_set_multiple(key, values):
    if values:
        postconf_set(key, ' '.join(values))
    else:
        postconf_del(key)

# Basic Postfix configuration settings using postconf.
#
# Params:
#   letsencrypt_home : Let's Encrypt home dir
def postconf_all(letsencrypt_home):
    postconf_set('biff',                         'no')
    postconf_set('broken_sasl_auth_clients',     'no')
    postconf_set('delay_warning_time',           '4h')
    postconf_set('inet_interfaces',              'all')
    postconf_set('lmtp_sasl_auth_enable',        'no')
    postconf_set('mydomain',                     mkhost.cfg.MY_HOST_DOMAIN)
    postconf_set('myhostname',                   "{}.{}".format(mkhost.cfg.MY_HOST_NAME, mkhost.cfg.MY_HOST_DOMAIN))
    postconf_del('mynetworks')
    postconf_set('mynetworks_style',             'host')
    postconf_set('myorigin',                     '$myhostname')
    # TODO test it
    postconf_set('recipient_delimiter',          '+')
    postconf_del('relay_domains')
    # TODO: relay host
    postconf_del('relayhost')

    postconf_set('smtp_sasl_auth_enable',        'no')
    postconf_set('smtp_tls_loglevel',            '1')
    postconf_set('smtp_tls_security_level',      'may')

    # TODO: reject_rbl_client zen.spamhaus.org ?
    postconf_set('smtpd_recipient_restrictions', 'permit_mynetworks permit_sasl_authenticated reject_unauth_destination')
    postconf_set('smtpd_relay_restrictions',     'permit_mynetworks permit_sasl_authenticated reject_unauth_destination')
    postconf_set('smtpd_sasl_auth_enable',       'no')
    postconf_set('smtpd_tls_auth_only',          'yes')
    postconf_set('smtpd_tls_cert_file',          mkhost.letsencrypt.cert_path(letsencrypt_home))
    postconf_set('smtpd_tls_key_file',           mkhost.letsencrypt.key_path(letsencrypt_home))
    postconf_set('smtpd_tls_loglevel',           '1')
    postconf_set('smtpd_tls_mandatory_ciphers',  'high')
    postconf_set('smtpd_tls_security_level',     'may')
    postconf_set('smtpd_tls_wrappermode',        'no')

    # The directory where local(8) UNIX-style mailboxes are kept. The default setting depends on the system type.
    # Specify a name ending in / for maildir-style delivery.
    #
    # Note: maildir delivery is done with the privileges of the recipient. If you use the mail_spool_directory
    # setting for maildir style delivery, then you must create the top-level maildir directory in advance.
    # Postfix will not create it.
    #
    # http://www.postfix.org/postconf.5.html#mail_spool_directory
    mail_spool_directory = postconf_get('mail_spool_directory') or '/var/mail/'
    logging.debug('mail_spool_directory: {}'.format(mail_spool_directory))
    if not mail_spool_directory.endswith('/'):
        postconf_set('mail_spool_directory', mail_spool_directory + '/')
    # TODO create user dirs

    postconf_set('smtpd_sasl_path',              'private/auth')

    # Only allow methods that support forward secrecy (Dovecot only).
    # http://www.postfix.org/postconf.5.html#smtpd_sasl_security_options
    postconf_set('smtpd_sasl_security_options',  'noanonymous forward_secrecy')

    # The SASL plug-in type that the Postfix SMTP server should use for authentication.
    # The available types are listed with the "postconf -a" command.
    # http://www.postfix.org/postconf.5.html#smtpd_sasl_type
    # TODO: check if dovecot is available! error if not.
    postconf_set('smtpd_sasl_type',              'dovecot')

    # TODO milter

    # virtual alias domains
    #
    # http://www.postfix.org/postconf.5.html#virtual_alias_domains
    postconf_set_multiple('virtual_alias_domains', mkhost.cfg_parser.get_alias_domains())

    # http://www.postfix.org/postconf.5.html#virtual_alias_maps
    postconf_set('virtual_alias_maps', "hash:{}".format(mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP))

    # virtual mailbox domains
    #
    # http://www.postfix.org/postconf.5.html#virtual_mailbox_domains
    postconf_set_multiple('virtual_mailbox_domains', mkhost.cfg.MAILBOXES.keys())

    # http://www.postfix.org/postconf.5.html#virtual_mailbox_maps
    postconf_set('virtual_mailbox_maps', "hash:{}".format(mkhost.cfg.POSTFIX_VIRTUAL_MAILBOX_MAP))

# Generates and writes out virtual alias map file (mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP).
def write_valias_map():
    mfwd = copy.deepcopy(mkhost.cfg.MAIL_FORWARDING)

    # Parse the existing virtual alias map file
    old_lines = []
    try:
        with open(mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP) as f:
            for line in map(lambda x: x.rstrip(), f):
                if mkhost.common.re_comment.match(line):
                    old_lines.append(line)
                elif mkhost.common.re_blank.match(line):
                    old_lines.append(line)
                else:
                    m = re_valias.match(line)

                    if m:
                        suser  = m.group(1)         # source user
                        sdom   = m.group(2)         # source domain
                        taddr1 = m.group(3)         # 1st target address
                        taddrs = list(filter(bool, map(lambda x: x.strip(), m.group(4).split(','))))

                        # logging.debug("suser  : {}#".format(suser))
                        # logging.debug("sdom   : {}#".format(sdom))
                        # logging.debug("taddr1 : {}#".format(taddr1))
                        # logging.debug("taddrs : {}#".format(taddrs))

                        saddr = "{}@{}".format(suser, sdom)     # source address
                        taddrs.insert(0,taddr1)
                        # logging.debug("taddrs : {}#".format(taddrs))

                        if (saddr in mfwd):
                            # logging.debug("mapping already exists: {}".format(saddr))
                            mto = mkhost.common.tolist(mfwd[saddr])
                            # logging.debug("mto: {}".format(mto))

                            # taddrs_set = set(taddrs)
                            # mto_set    = set(mto)
                            # logging.debug("taddrs_set: {}".format(taddrs_set))
                            # logging.debug("   mto_set: {}".format(mto_set))

                            if (len(taddrs) == len(mto)) and (set(taddrs) == set(mto)):
                                logging.debug("mapping already exists: {} => {}".format(saddr, mto))
                                old_lines.append(line)
                                del mfwd[saddr]
                            else:
                                logging.info("delete mapping: {} => {}".format(saddr, taddrs))
                        else:
                            logging.info("delete mapping: {}".format(saddr))
                    else:
                        logging.warning("{}: invalid line: {}".format(mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP, line))
    except FileNotFoundError:
        logging.warning("Postfix virtual alias map file does not exist: {}".format(mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP))

    # create new virtual alias map file
    with tempfile.NamedTemporaryFile(mode="wt", prefix="mkhost-", delete=True) as f:
        logging.debug("temp file: {}".format(f.name))
        if old_lines:
            print(os.linesep.join(old_lines), file=f)
        if mfwd:
            print(mkhost.common.mkhost_header(), file=f)
            for x in mfwd:
                ys = mkhost.common.tolist(mfwd[x])
                logging.info("create mapping: {} => {}".format(x, ys))
                print("{}    {}".format(x, ", ".join(ys)), file=f)

        # overwrite old user db file
        if not mkhost.common.get_dry_run():
            f.flush()
            shutil.copyfile(f.name, mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP)
            mkhost.common.execute_cmd(["postmap", mkhost.cfg.POSTFIX_VIRTUAL_ALIAS_MAP])

# Generates and writes out virtual mailbox map file (mkhost.cfg.POSTFIX_VIRTUAL_MAILBOX_MAP).
def write_vmailbox_map():
    vboxes = mkhost.cfg_parser.get_virtual_mailboxes()

    # Parse the existing virtual mailbox map file
    old_lines = []
    try:
        with open(mkhost.cfg.POSTFIX_VIRTUAL_MAILBOX_MAP) as f:
            for line in map(lambda x: x.rstrip(), f):
                if mkhost.common.re_comment.match(line):
                    old_lines.append(line)
                elif mkhost.common.re_blank.match(line):
                    old_lines.append(line)
                else:
                    m = re_vmailbox.match(line)

                    if m:
                        username = m.group(1)
                        domain   = m.group(2)
                        path     = m.group(3)

                        logging.debug("username : {}#".format(username))
                        logging.debug("domain   : {}#".format(domain))
                        logging.debug("path     : {}#".format(path))

                        # TODO: make the 2nd lookup more effective?...
                        if (domain in mkhost.cfg.MAILBOXES) and (username in mkhost.cfg.MAILBOXES[domain]):
                            logging.debug("mailbox already exists: {}@{}".format(username, domain))
                            old_lines.append(line)
                            vboxes.remove("{}@{}".format(username, domain))
                        else:
                            logging.info("delete mailbox: {}@{}".format(username, domain))
                    else:
                        logging.warning("{}: invalid line: {}".format(mkhost.cfg.POSTFIX_VIRTUAL_MAILBOX_MAP, line))
    except FileNotFoundError:
        logging.warning("Postfix virtual mailbox map file does not exist: {}".format(mkhost.cfg.POSTFIX_VIRTUAL_MAILBOX_MAP))

    # create new virtual mailbox map file
    with tempfile.NamedTemporaryFile(mode="wt", prefix="mkhost-", delete=True) as f:
        logging.debug("temp file: {}".format(f.name))
        if old_lines:
            print(os.linesep.join(old_lines), file=f)
        if vboxes:
            print(mkhost.common.mkhost_header(), file=f)
            for x in vboxes:
                xp = mkhost.common.parse_addr(x)
                logging.info("create mailbox: {}@{}".format(xp[0],xp[1]))
                print("{}@{}    {}/{}/mail/".format(xp[0],xp[1],xp[1],xp[0]), file=f)

        # overwrite old user db file
        if not mkhost.common.get_dry_run():
            f.flush()
            shutil.copyfile(f.name, mkhost.cfg.POSTFIX_VIRTUAL_MAILBOX_MAP)

# Installs and configures Postfix.
#
# Params:
#   letsencrypt_home : Let's Encrypt home dir
def install(letsencrypt_home):
    mkhost.common.install_pkgs(["postfix"])
    write_vmailbox_map()
    write_valias_map()
    postconf_all(letsencrypt_home)
