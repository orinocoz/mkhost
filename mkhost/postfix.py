import mkhost.common

def postconf_set(key, value):
    mkhost.common.execute_cmd(["postconf", "-v", "-e", "{}={}".format(key,value)])

# Installs and configures Postfix.
def install():
    mkhost.common.install_pkgs(["postfix"])

    postconf_set('smtp_tls_security_level',  'may')

    postconf_set('smtpd_tls_security_level', 'may')
    postconf_set('smtpd_tls_wrappermode',    'no')
    postconf_set('smtpd_tls_auth_only',      'yes')

    # postconf_set('', '')
