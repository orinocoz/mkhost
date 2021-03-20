import mkhost.common

def postconf_del(key):
    mkhost.common.execute_cmd(["postconf", "-v", "-#", "{}".format(key)])

def postconf_set(key, value):
    mkhost.common.execute_cmd(["postconf", "-v", "-e", "{}={}".format(key,value)])

# Installs and configures Postfix.
def install():
    mkhost.common.install_pkgs(["postfix"])

    postconf_set('broken_sasl_auth_clients',     'no')
    postconf_set('lmtp_sasl_auth_enable',        'no')
    postconf_del('relay_domains')

    postconf_set('smtp_sasl_auth_enable',        'no')
    postconf_set('smtp_tls_security_level',      'may')

    postconf_set('smtpd_recipient_restrictions', 'permit_mynetworks reject_unauth_destination')
    postconf_set('smtpd_relay_restrictions',     'permit_mynetworks permit_sasl_authenticated reject_unauth_destination')
    postconf_set('smtpd_sasl_auth_enable ',      'no')
    postconf_set('smtpd_tls_auth_only',          'yes')
    postconf_set('smtpd_tls_security_level',     'may')
    postconf_set('smtpd_tls_wrappermode',        'no')

    # postconf_set('', '')
