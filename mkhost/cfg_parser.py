import logging

import mkhost.cfg
import mkhost.common

# Given MAIL_FORWARDING (in the config file), compute the outgoing addresses (those mapped to, but
# not mapped from). Can include mailboxes and 3rd party addresses.
def get_fwd_dst_addresses():
    vals2     = map(mkhost.common.tolist, mkhost.cfg.MAIL_FORWARDING.values())
    vals      = set(x for ys in vals2 for x in ys)
    keys      = mkhost.cfg.MAIL_FORWARDING.keys()
    outgoing  = vals.difference(keys)
    logging.debug("get_fwd_dst_addresses: {}".format(outgoing))
    return outgoing

# Given MAILBOXES and MAIL_FORWARDING (in the config file), compute the
# virtual alias domains (mailbox-less domains used for mail forwarding).
#
# http://www.postfix.org/postconf.5.html#virtual_alias_domains
def get_alias_domains():
    keydoms = mkhost.common.addr2dom(mkhost.cfg.MAIL_FORWARDING.keys())
    aliased = keydoms.difference(mkhost.cfg.MAILBOXES.keys())
    logging.debug("get_alias_domains: {}".format(aliased))
    return aliased

# Given MAILBOXES (in the config file), compute the virtual mailbox
# domains (those which can contain mailboxes).
#
# http://www.postfix.org/postconf.5.html#virtual_mailbox_domains
def get_mailbox_domains():
    return set(mkhost.cfg.MAILBOXES.keys())

# Given MAILBOXES and FORWARDING (in the config file), compute the
# virtual mailbox set (hosted virtual mailboxes).
def get_virtual_mailboxes():
    mailboxes = set("{}@{}".format(x,d) for d, xs in mkhost.cfg.MAILBOXES.items() for x in xs)
    logging.debug("get_virtual_mailboxes: {}".format(mailboxes))
    return mailboxes

def validate():
    if not mkhost.cfg.LOCAL_MAILBOX_BASE.endswith('/'):
        raise Exception("LOCAL_MAILBOX_BASE must end with '/' (maildir-style delivery of local mail is enforced)")

    # check if all virtual domain mailboxes declared on the right hand side of MAIL_FORWARDING
    # are declared in MAILBOXES
    outhosted = mkhost.common.filter_addr_in_domain(mkhost.cfg.MAILBOXES.keys(), get_fwd_dst_addresses())
    # logging.debug("outhosted (1): {}".format(outhosted))
    outhosted = outhosted.difference(get_virtual_mailboxes())
    # logging.debug("outhosted (2): {}".format(outhosted))
    if outhosted:
        raise Exception("Extra addresses on the right hand side in MAIL_FORWARDING: {}. They belong to MAILBOXES domains. Did you forget to declare them in MAILBOXES?".format(outhosted))
