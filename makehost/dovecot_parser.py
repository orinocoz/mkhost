##############################################################################
# Dovecot configuration parser
#
# https://doc.dovecot.org/configuration_manual/config_file/config_file_syntax/
#
# KNOWN BUGS
#
#   1. External config files: https://doc.dovecot.org/configuration_manual/config_file/config_file_syntax/#external-config-files
#      are not supported.
#   2. Environment variables: https://doc.dovecot.org/configuration_manual/config_file/config_file_syntax/#environment-variables
#      are not supported.
##############################################################################

from dataclasses import dataclass
from typing import List

# A piece of configuration encountered in the file.
@dataclass
class Item:
    filename : str      # File where this is defined (full path)
    lfirst   : int      # First line of this item
    lcnt     : int      # Number of lines this item spans

# Whitespace-only line
@dataclass
class BlankLine(Item):
    pass

# A single line comment, starting with a hash (#)
@dataclass
class CommentLine(Item):
    pass

# include statement, for example:
#
# !include local.conf
# !include /path/to/another.conf
# !include conf.d/*.conf
@dataclass
class Include(Item):
    what : str

# include_try statement, for example:
#
# !include_try local.conf
# !include_try /path/to/another.conf
# !include_try conf.d/*.conf
@dataclass
class IncludeTry(Item):
    what : str

# Right-hand-side value in a simple setting of the form:
#
# settings_key = settings_value
@dataclass
class Value(Item):
    pass

# Value of the form:
#
# </path/to/file
#
# (absolute) or:
#
# <path/to/file
#
# (relative to the current file).
@dataclass
class FromFile(Value):
    rfile : str

# A string value. This can still contain variable expansion like:
#
# key2 = $key value2
@dataclass
class StringValue(Value):
    s : str

# A simple setting of the form:
#
# settings_key = settings_value
@dataclass
class KeyValue(Item):
    key      : str
    value    : Value

# A section with an optional name
#
# section optional_name {
#   section_setting_key = section_setting_value
#   subsection optional_subname {
#     subkey = subvalue
#   }
# }
@dataclass
class Section(Item):
    name     : str
    body     : List[Item]
