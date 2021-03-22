import logging

import mkhost.common
import mkhost.cfg

# Given an e-mail address (or a collection thereof), returns the domain (or a set thereof).
def addr2dom(addr):
    return x.partition('@')[2] if isinstance(addr,str) else set(map(lambda x: x.partition('@')[2], addr))

# Given a set of domains and a set of addresses, returns the subset of addresses which belong
# to any of the given domains.
def filter_addr_in_domain(domains, addresses):
    xs = set(filter(lambda x: addr2dom(x) in domains, addresses))
    logging.debug("filter_addr_in_domain: {} + {} => {}".format(domains, addresses, xs))
    return xs

# Given ADDRESS_MAP (in the config file), compute the outgoing addresses (those mapped to, but
# not mapped from).
def get_outgoing_addresses():
    vals2     = map(lambda x : x if isinstance(x,list) else [x], mkhost.cfg.ADDRESS_MAP.values())
    vals      = set(x for ys in vals2 for x in ys)
    keys      = mkhost.cfg.ADDRESS_MAP.keys()
    outgoing  = vals.difference(keys)
    logging.debug("get_outgoing_addresses: {}".format(outgoing))
    return outgoing

# Given HOSTED_DOMAINS and ADDRESS_MAP (in the config file), compute the
# virtual alias domains (mailbox-less domains used for mail forwarding).
#
# http://www.postfix.org/postconf.5.html#virtual_alias_domains
def get_alias_domains():
    keydoms = addr2dom(mkhost.cfg.ADDRESS_MAP.keys())
    aliased = keydoms.difference(mkhost.cfg.HOSTED_DOMAINS)
    logging.debug("get_alias_domains: {}".format(aliased))
    return aliased

# Given HOSTED_DOMAINS and ADDRESS_MAP (in the config file), compute the
# virtual mailbox set (hosted virtual mailboxes).
def get_virtual_mailboxes():
    outhosted = filter_addr_in_domain(mkhost.cfg.HOSTED_DOMAINS, get_outgoing_addresses())
    logging.debug("get_virtual_mailboxes: {}".format(outhosted))
    return outhosted
