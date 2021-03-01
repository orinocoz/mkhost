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
import glob
import logging
import os.path
import re
import typing

re_blank         = re.compile('^\s*$', re.ASCII)
re_comment       = re.compile('^\s*\#.*$', re.ASCII)
re_setting       = re.compile('^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$', re.ASCII)
re_from_file     = re.compile('^\s*\<([-A-Za-z0-9_]+)\s*$', re.ASCII)
re_include       = re.compile('^\s*\!include\s+([-A-Za-z0-9_,.?!()*/]+)\s*$', re.ASCII)
re_include_try   = re.compile('^\s*\!include\_try\s+([-A-Za-z0-9_,.?!()*/]+)\s*$', re.ASCII)
re_section_anon  = re.compile('^\s*([-A-Za-z0-9_]+)\s*\{\s*$', re.ASCII)
re_section_named = re.compile('^\s*([-A-Za-z0-9_]+)\s+([-" !A-Za-z0-9_/]+?)\s*\{\s*$', re.ASCII)
re_section_close = re.compile('^\s*\}\s*$', re.ASCII)

# A piece of configuration encountered in the file.
#
# frozen=True => this is immutable.
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class Item:
    filename : str      # File where this is defined (full path)
    lfirst   : int      # First line of this item (1-based)
    lcnt     : int      # Number of lines this item spans

    INDENT_1 = '  '     # indentation

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "{}:{}-{}".format(filename, lfirst, lfirst+lcnt-1)

# Whitespace-only line
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class BlankLine(Item):

    def __str__(self, indent=0):
        return ""

# A single line comment, starting with a hash (#)
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class CommentLine(Item):

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "#"

# Right-hand-side value in a simple setting of the form:
#
# settings_key = settings_value
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class Value(Item):

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "<value>"

# Value of the form:
#
# </path/to/file
#
# (absolute) or:
#
# <path/to/file
#
# (relative to the current file).
# rfile is the canonizalized filename (os.path.realpath).
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class FromFile(Value):
    rfile : str

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "< {}".format(self.rfile)

# A string value. This can still contain variable expansion like:
#
# key2 = $key value2
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class StringValue(Value):
    sval : str

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "{}".format(self.sval)

# A simple setting of the form:
#
# settings_key = settings_value
@dataclasses.dataclass(init=True, repr=True, eq=True, frozen=True)
class KeyValue(Item):
    key      : str
    value    : Value

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "{} = {}".format(self.key, self.value)

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
    sec_type : str          # "section"
    name     : str          # "optional_name"
    body     : typing.List[Item]

    def __str__(self, indent=0):
        return (self.INDENT_1 * indent) + "{} {} {{".format(self.sec_type, self.name or '') + os.linesep +  \
                   ((self.INDENT_1 * indent) + os.linesep).join(                                            \
                       map(lambda x: x.__str__(indent=indent+1),                                            \
                           filter(lambda x: not isinstance(x, (BlankLine, CommentLine)), self.body)))   +   \
                   (self.INDENT_1 * indent) + os.linesep +                                                  \
                   (self.INDENT_1 * indent) + "}"

# Parses an !include or !include_try statement.
#
# Params:
#   incl_try : True if !include_try, False otherwise.
#
# Returns: a concatenated list of Item.
def parse_include(filename, include_pattern, incl_try, parsed_files, visited_files):
    indent = "  " * len(visited_files)
    logging.debug("{}parse dovecot include{} in {}: {}".format(indent, "_try" if incl_try else "    ", filename, include_pattern))
    logging.debug("{}visited_files: {}".format(indent, ", ".join(visited_files)))

    dirname     = os.path.dirname(filename)
    pattern_abs = os.path.join(dirname, include_pattern)    # works even if include_pattern is absolute!
    filelist    = sorted(glob.glob(pattern_abs, recursive=False))
    item_list   = []

    for f in filelist:
        item_list.extend(parse_config_file(f, incl_try, parsed_files, visited_files)[0])

    return item_list

# Parses a single configuration file. This is recursive, i.e. !include and !include_try are followed.
#
# Params:
#
#   ignore_io_errors : whether to ignore non-existent or inaccessible files
#   parsed_files     : a map of: filename -> (item list, line list).
#                      These are the completed files.
#   visited_files    : a (frozen) set of files visited in this recursive
#                      call
#
# Returns a pair: (list of Items, list of lines).
#         The 1st can be shorter than the 2nd (not every line
#         represents a top-level item).
def parse_config_file(filename, ignore_io_errors, parsed_files, visited_files):
    filename = os.path.realpath(filename)       # canonicalize the file name
    indent   = "  " * len(visited_files)
    logging.debug("{}parse dovecot config file: {}".format(indent, filename))
    logging.debug("{}visited_files: {}".format(indent, ", ".join(visited_files)))

    if filename in visited_files:
        raise ValueError("Error parsing Dovecot configuration: cyclic include: {}".format(filename))
    if filename in parsed_files:
        return parsed_files[filename]

    # read the whole file into memory
    line_list = []
    with open(filename) as f:
        line_list = [x.strip() for x in f.readlines()]

    # Stack of open sections (which grows at the head, i.e. new items are
    # prepended at the beginning).
    # Each item is a tuple: (lfirst, sec_type, name, list of Item).
    # Last item is a sentinel which represents the whole file.
    section_stack = [(1, None, filename, [])]

    for i, line in enumerate(line_list, start=1):
        logging.debug("{}parse line {: 5d}: {}".format(indent, i, line))
        item = None

        if re_blank.match(line):
            item = BlankLine(filename=filename, lfirst=i, lcnt=1)
        elif re_comment.match(line):
            item = CommentLine(filename=filename, lfirst=i, lcnt=1)
        elif re_section_close.match(line):
            # close the current section
            if (2 <= len(section_stack)):
                csec = section_stack.pop(0)
                item = Section(filename=filename, lfirst=csec[0], lcnt=(i+1-csec[0]), sec_type=csec[1], name=csec[2], body=csec[3])
            else:
                raise ValueError("Error parsing Dovecot configuration: unexpected section end at {}:{}: {}".format(filename, i, line))
        else:
            m = re_include_try.match(line)
            ignore_errors = True
            if not m:
                m = re_include.match(line)
                ignore_errors = False
            if m:
                include_pattern = m.group(1)
                included_items  = parse_include(filename, include_pattern, ignore_errors, parsed_files, visited_files.union([filename]))
                section_stack[0][3].extend(included_items)
            else:
                m = re_section_anon.match(line)
                sec_name = None
                if not m:
                    m = re_section_named.match(line)
                    if m:
                        sec_name = m.group(2)
                if m:
                    # open a new section
                    section_stack.insert(0, (i, m.group(1), sec_name, []))
                else:
                    m = re_setting.match(line)
                    if m:
                        skey   = m.group(1)
                        svalue = m.group(2)

                        m2 = re_from_file.match(svalue)
                        if m2:
                            target_file = os.path.join(filename, m2.group(1))   # works even if target file path is absolute!
                            target_file = os.path.realpath(target_file)
                            item = KeyValue(filename=filename, lfirst=i, lcnt=1, key=skey, value=FromFile(filename=filename, lfirst=i, lcnt=1, rfile=target_file))
                        else:
                            item = KeyValue(filename=filename, lfirst=i, lcnt=1, key=skey, value=StringValue(filename=filename, lfirst=i, lcnt=1, sval=svalue))
                    else:
                        raise ValueError("Error parsing Dovecot configuration: unknown syntax at {}:{}: {}".format(filename, i, line))

        # append item to the last open section
        if item:
            if not isinstance(item, (BlankLine, CommentLine)):
                logging.debug("{}              ==> {}".format(indent, item))
            section_stack[0][3].append(item)

    parsed_files[filename] = (section_stack[-1][3], line_list)
    return parsed_files[filename]

# Parses Dovecot configuration file. This is recursive, i.e. !include and !include_try are followed.
def parse_dovecot_config(filename):
    # A dictionary of parsed files. Each of them is mapped
    # onto a tuple: (list of lines, list of Item).
    parsed_files = dict()

    (items, lines) = parse_config_file(filename, False, parsed_files, frozenset())

    pretty_str = os.linesep.join(
        map(lambda x: "{}".format(x),
            filter(lambda x: not isinstance(x, (BlankLine, CommentLine)), items)))
    logging.debug(pretty_str)
