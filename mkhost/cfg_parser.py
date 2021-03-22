import logging

import mkhost.common
import mkhost.cfg

# Given an e-mail address (or a collection thereof), returns the domain (or a set thereof).
def addr2dom(addr):
    return addr.partition('@')[2] if isinstance(addr,str) else set(map(lambda x: x.partition('@')[2], addr))

# Given a set of domains and a set of addresses, returns the subset of addresses which belong
# to any of the given domains.
def filter_addr_in_domain(domains, addresses):
    xs = set(filter(lambda x: addr2dom(x) in domains, addresses))
    logging.debug("filter_addr_in_domain: {} + {} => {}".format(domains, addresses, xs))
    return xs

# Given MAIL_FORWARDING (in the config file), compute the outgoing addresses (those mapped to, but
# not mapped from).
def get_outgoing_addresses():
    vals2     = map(lambda x : x if isinstance(x,list) else [x], mkhost.cfg.MAIL_FORWARDING.values())
    vals      = set(x for ys in vals2 for x in ys)
    keys      = mkhost.cfg.MAIL_FORWARDING.keys()
    outgoing  = vals.difference(keys)
    logging.debug("get_outgoing_addresses: {}".format(outgoing))
    return outgoing

# Given MAILBOXES and MAIL_FORWARDING (in the config file), compute the
# virtual alias domains (mailbox-less domains used for mail forwarding).
#
# http://www.postfix.org/postconf.5.html#virtual_alias_domains
def get_alias_domains():
    keydoms = addr2dom(mkhost.cfg.MAIL_FORWARDING.keys())
    aliased = keydoms.difference(mkhost.cfg.MAILBOXES.keys())
    logging.debug("get_alias_domains: {}".format(aliased))
    return aliased

# Given MAILBOXES and FORWARDING (in the config file), compute the
# virtual mailbox set (hosted virtual mailboxes).
def get_virtual_mailboxes():
    mailboxes = set("{}@{}".format(x,d) for d, xs in mkhost.cfg.MAILBOXES.items() for x in xs)
    logging.debug("mailboxes: {}".format(mailboxes))
    outhosted = filter_addr_in_domain(mkhost.cfg.MAILBOXES.keys(), get_outgoing_addresses())
    logging.debug("outhosted (1): {}".format(outhosted))
    outhosted = outhosted.difference(mailboxes)
    logging.debug("outhosted (2): {}".format(outhosted))
    if outhosted:
        logging.warning("Extra addresses on the right hand side in MAIL_FORWARDING: {}. They belong to MAILBOXES domains. Did you want to declare them in MAILBOXES?".format(outhosted))
    logging.debug("get_virtual_mailboxes: {}".format(mailboxes))
    return mailboxes
