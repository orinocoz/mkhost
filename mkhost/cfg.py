##############################################################################
# The configuration file.
#
# Edit below as needed.
##############################################################################
#
# A simple, 1-component hostname of the target machine.
MY_HOST_NAME = "my-host"

# Domain of the target machine, without the hostname.
#
# Thus, the FQDN (fully-qualified domain name) of the target machine will be:
#
#   MY_HOST_NAME . MY_HOST_DOMAIN
#
# This FQDN will be used to obtain Let's Encrypt certificate.
# This must correspond to your DNS.
MY_HOST_DOMAIN = "my-domain.tld"

# Hosted (virtual) mail domains. MX DNS record for each of them should point
# to MY_HOST_NAME . MY_HOST_DOMAIN . You can setup CNAME records too, if you
# like (not required for mail).
GUEST_DOMAINS = ["a-hosted.com", "b-hosted.org", "something-else.com"]

# E-mail address mapping for mail forwarding. A single address can be mapped
# to 1 or more other addresses, possibly on multiple domains.
#
# Note: you don't need to own those domains or mailboxes!
#       You can forward anywhere.
ADDRESS_MAP = {
    "alice@a-hosted.com"            : "bob@something-else.com",
    "bob@a-hosted.com"              : [ "alice@b-hosted.org", "bob@something-else.com" ],
    "bob.lastname@b-hosted.org"     : "bob@b-hosted.org",
    "mailtunnel@something-else.com" : "astray@gmail.com"
}
