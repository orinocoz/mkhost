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

import dataclasses
import logging
import os.path
import re
import typing

re_blank        = re.compile('^\s*$', re.ASCII)
re_comment      = re.compile('^\s*\#.*$', re.ASCII)
re_include      = re.compile('^\s*\!include\s+([-A-Za-z0-9_,.?!()*/]+)$', re.ASCII)
re_include_try  = re.compile('^\s*\!include\_try\s+([-A-Za-z0-9_,.?!()*/]+)$', re.ASCII)
re_section_anon = re.compile('^\s*([-A-Za-z0-9_]+)\s*\{\s*$', re.ASCII)
re_section_close= re.compile('^\s*\}\s*$', re.ASCII)

# A piece of configuration encountered in the file.
#
# frozen=True => this is immutable.
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class Item:
    filename : str      # File where this is defined (full path)
    lfirst   : int      # First line of this item (1-based)
    lcnt     : int      # Number of lines this item spans

# Whitespace-only line
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class BlankLine(Item):
    pass

# A single line comment, starting with a hash (#)
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class CommentLine(Item):
    pass

# include statement, for example:
#
# !include local.conf
# !include /path/to/another.conf
# !include conf.d/*.conf
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class Include(Item):
    what : str

# include_try statement, for example:
#
# !include_try local.conf
# !include_try /path/to/another.conf
# !include_try conf.d/*.conf
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class IncludeTry(Item):
    what : str

# Right-hand-side value in a simple setting of the form:
#
# settings_key = settings_value
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
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
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class FromFile(Value):
    rfile : str

# A string value. This can still contain variable expansion like:
#
# key2 = $key value2
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class StringValue(Value):
    s : str

# A simple setting of the form:
#
# settings_key = settings_value
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
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
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class Section(Item):
    name     : str
    body     : typing.List[Item]

# Parses a single configuration file. This is not recursive, i.e.
# includes are not followed.
#
# Returns a pair: (list of Items, list of lines).
#         The 1st can be shorter than the 2nd (not every line
#         represents a top-level item).
def parse_config_file(filename):
    line_list = []

    # read the whole file into memory
    with open(filename) as f:
        line_list = [x.strip() for x in f.readlines()]

    # Stack of open sections (which grows at the head, i.e. new items are
    # prepended at the beginning).
    # Each item is a tuple: (lfirst, name, list of Item).
    # Last item is a sentinel which represents the whole file.
    section_stack = [(1, filename, [])]

    for i, line in enumerate(line_list, start=1):
        logging.debug("parse line {: 5d}: {}".format(i, line))
        item = None

        if re_blank.match(line):
            item = BlankLine(filename=filename, lfirst=i, lcnt=1)
        elif re_comment.match(line):
            item = CommentLine(filename=filename, lfirst=i, lcnt=1)
        elif re_section_close.match(line):
            # close the current section
            if (2 <= len(section_stack)):
                csec = section_stack.pop(0)
                item = Section(filename=filename, lfirst=csec[0], lcnt=(i+1-csec[0]), name=csec[1], body=csec[2])
            else:
                raise ValueError("Error parsing Dovecot configuration: unexpected section end at {}:{}: {}".format(filename, i, line))
        else:
            m = re_include_try.match(line)
            if m:
                item = IncludeTry(filename=filename, lfirst=i, lcnt=1, what=m.group(1))
            else:
                m = re_include.match(line)
                if m:
                    item = Include(filename=filename, lfirst=i, lcnt=1, what=m.group(1))
                else:
                    m = re_section_anon.match(line)
                    if m:
                        # open a new section
                        section_stack.insert(0, (i, None, []))
                    else:
                        raise ValueError("Error parsing Dovecot configuration: unknown syntax at {}:{}: {}".format(filename, i, line))

        # append the item to the last open section
        if item:
            logging.debug("              ==> {}".format(item))
            section_stack[0][2].append(item)

    return (section_stack[-1][2], line_list)

# Parses Dovecot configuration file. This is recursive, i.e.
# !include and !include_try are followed.
def parse_dovecot_config(filename):
    filename = os.path.realpath(filename)
    visited_files = set()

    (items, lines) = parse_config_file(filename)
    for it in items:
        logging.debug("Item: {}".format(it))