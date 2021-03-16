import logging

import mkhost.common
import mkhost.cfg

# Given HOSTED_DOMAINS and ADDRESS_MAP (in the config file), compute the
# virtual mailbox set.
def get_virtual_mailboxes():
    logging.debug("HOSTED_DOMAINS: {}".format(mkhost.cfg.HOSTED_DOMAINS))
    logging.debug("ADDRESS_MAP: {}".format(mkhost.cfg.ADDRESS_MAP))

    vals2 = map(lambda x : x if isinstance(x,list) else [x], mkhost.cfg.ADDRESS_MAP.values())
    logging.debug("vals2: {}".format(vals2))
    vals  = set(x for ys in vals2 for x in ys)
    logging.debug("vals : {}".format(vals))
    keys  = mkhost.cfg.ADDRESS_MAP.keys()
    logging.debug("keys : {}".format(keys))
    dest_ext    = vals.difference(keys)
    logging.debug("dest_ext : {}".format(dest_ext))
    dest_hosted = set(filter(lambda x: x.partition('@')[2] in mkhost.cfg.HOSTED_DOMAINS, vals))
    logging.debug("dest_hosted : {}".format(dest_hosted))

    return dest_hosted
