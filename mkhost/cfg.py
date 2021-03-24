##############################################################################
# The configuration file.
#
# Edit below as needed.
##############################################################################

# A simple, 1-component hostname of the target machine.
# This must correspond to your DNS.
MY_HOST_NAME = "my-host"

# Domain of the target machine, without the hostname.
#
# Thus, the FQDN (fully-qualified domain name) of the target machine will be:
#
#   MY_HOST_NAME . MY_HOST_DOMAIN
#
# This FQDN will be used to obtain Let's Encrypt certificate.
# This must correspond to your DNS.
MY_HOST_DOMAIN = "example.com"

# List of mailboxes (per domain).
MAILBOXES = {
    "b-server": ["user1", "user2"],
    "c-server": ["eve"]
}

# E-mail address mapping for mail forwarding. A single address can be mapped
# to 1 or more other addresses, possibly on multiple domains.
#
# Note: you don't need to own those domains or mailboxes!
#       You can forward anywhere.
MAIL_FORWARDING = {
    "alice@a-server"                : "postmaster@b-server",
    "postmaster@b-server"           : ["alice@a-server", "bob@b-server"],
    "bob@a-server"                  : "bob@b-server",
    "mailtunnel@a-server"           : "endpoint@somewhere-else",
    "bob@b-server"                  : "eve@c-server",
    "postmaster@my-domain.tld"      : "postmaster@b-server"
}

# List of mail protocols to enable in Dovecot. This is mapped directly to
# https://doc.dovecot.org/settings/core/#protocols
DOVECOT_PROTOCOLS = ["imap", "pop3"]

# Whether Dovecot should listen on all interfaces (False) or just the
# localhost (True). If all your users are local, then setting this to
# True will improve security.
DOVECOT_LOOPBACK_ONLY = False

# Dovecot users database
DOVECOT_USERS_DB = "/etc/dovecot/users.mkhost"

# Postfix virtual mailbox map file.
#
# http://www.postfix.org/postconf.5.html#virtual_mailbox_maps
POSTFIX_VIRTUAL_MAILBOX_MAP = "/etc/postfix/vmailbox.mkhost"

# Postfix virtual alias map file.
#
# http://www.postfix.org/postconf.5.html#virtual_alias_maps
POSTFIX_VIRTUAL_ALIAS_MAP = "/etc/postfix/valias.mkhost"
