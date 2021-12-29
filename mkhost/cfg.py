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

# Fully-qualified domain name.
MY_HOST_FULLNAME = (MY_HOST_NAME + "." + MY_HOST_DOMAIN)

# E-mail address to use with the SSL/TLS certificate.
X509_EMAIL = ("x509" + "@" + MY_HOST_FULLNAME)

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

# Postfix mail spool directory (aka directory where local mail is stored).
# Specify a name ending in / for maildir-style delivery.
#
# http://www.postfix.org/postconf.5.html#mail_spool_directory
LOCAL_MAILBOX_BASE = "/var/mail/"

# System user who owns virtual mail files.
# It will be created, if missing.
VIRTUAL_MAIL_USER = 'mkhost-mailv'

# Postfix virtual mailbox base (aka directory where virtual mail is stored).
# This is used by Dovecot, too.
#
# http://www.postfix.org/postconf.5.html#virtual_mailbox_base
VIRTUAL_MAILBOX_BASE = "/var/mail-virtual/"

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

# Directory where OpenDKIM will store domain keys.
OPENDKIM_KEYS = "/etc/opendkim/mkhost/"

# OpenDKIM config file
OPENDKIM_CONF     = "/etc/opendkim.conf"
OPENDKIM_KEYTABLE = "/etc/opendkim-keytable.mkhost"
