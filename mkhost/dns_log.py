import logging
import os

# Log of changes to be applied to DNS (externally).
class DNSLog:
    def __init__(self):
        # A list of DNS records (to be printed at the end).
        self.records = []

    def add_record(self, rec):
        self.records.append(rec)

    def __str__(self):
        return os.linesep.join(self.records)
