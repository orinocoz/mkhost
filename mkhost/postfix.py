import logging

import mkhost.cfg
import mkhost.common
import mkhost.letsencrypt

def postconf_del(key):
    mkhost.common.execute_cmd(["postconf", "-v", "-#", "{}".format(key)])

def postconf_get(key):
    return mkhost.common.execute_cmd(["postconf", "-h", "{}".format(key)])[0]

def postconf_set(key, value):
    mkhost.common.execute_cmd(["postconf", "-v", "-e", "{}={}".format(key,value)])

# Installs and configures Postfix.
#
# Params:
#   letsencrypt_home : Let's Encrypt home dir
def install(letsencrypt_home):
    mkhost.common.install_pkgs(["postfix"])

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
