import datetime
import logging
import os
import subprocess
import sys
import threading

##############################################################################
# Common settings
##############################################################################

_version_major   = 0
_version_minor   = 1
_dry_run         = True
_verbose         = False
_non_interactive = False
_run_ts          = datetime.datetime.now(datetime.timezone.utc)     # timestamp of this run

# Returns the version number as a pair (major, minor)
def get_version():
    return (_version_major, _version_minor)

def get_dry_run():
    return _dry_run

def set_dry_run(b):
    global _dry_run
    _dry_run = bool(b)
    logging.debug("_dry_run: {}".format(_dry_run))

def get_non_interactive():
    return _non_interactive

def set_non_interactive(b):
    global _non_interactive
    _non_interactive = bool(b)
    logging.debug("_non_interactive: {}".format(_non_interactive))

def get_verbose():
    return _verbose

def set_verbose(b):
    global _verbose
    _verbose = bool(b)
    logging.debug("_verbose: {}".format(_verbose))

def get_run_ts():
    return _run_ts

##############################################################################
# Common functions
##############################################################################

def _stream_reader(stream, handlers):
    for line in iter(stream.readline, b''):
        for h in handlers:
            h(line)

# Executes a system command in an interactive way.
# cmdline must be a list.
# Returns the list of resulting output lines.
def execute_cmd_interactive(cmdline):
    logging.info(" ".join(cmdline))

    proc = subprocess.Popen(
               cmdline,
               stdin=sys.stdin,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               check=True,
               universal_newlines=True)

    out_lines  = []
    out_reader = threading.Thread(target=_stream_reader, daemon=True,
                     args=(proc.stdout, [print, out_lines.append]))
    err_lines  = []
    err_reader = threading.Thread(target=_stream_reader, daemon=True,
                     args=(proc.stdout, [lambda x: print(x,file=sys.stderr), err_lines.append]))

    for t in (err_reader, out_reader):
        t.start()

    # wait for the process to terminate
    proc.wait()

    # join the reader threads
    for t in (err_reader, out_reader):
        t.join()

    # logging.debug("result: {}".format(result))
    # logging.debug("result.stderr: {}".format(result.stderr))
    # logging.debug("result.stdout: {}".format(result.stdout))
    # err_lines = result.stderr.splitlines() if result.stderr else []
    # out_lines = result.stdout.splitlines() if result.stdout else []

    for x in err_lines:
        logging.warning("E: {}".format(x))
    for x in out_lines:
        logging.debug("E: {}".format(x))
    return out_lines

# Executes a system command in a non-interactive way (batch).
# cmdline must be a list.
# Returns the list of resulting output lines.
def execute_cmd_batch(cmdline, input=None):
    logging.info(" ".join(cmdline))

    proc_result = subprocess.run(
                        cmdline,
                        input=input,
                        capture_output=True,
                        check=True,
                        universal_newlines=True)

    err_lines = result.stderr.splitlines()
    out_lines = result.stdout.splitlines()

    for x in err_lines:
        logging.warning(x)
    for x in out_lines:
        logging.debug(x)

    return out_lines

# Executes a system command.
# cmdline must be a list.
# Returns the list of resulting output lines.
def execute_cmd(cmdline):
    if get_non_interactive():
        return execute_cmd_batch(cmdline)
    else:
        return execute_cmd_interactive(cmdline)

# Returns the apt-get command with some default arguments applied.
# A list.
def apt_get_cmd(*args):
    return ["apt-get"]                                          +       \
               (["--dry-run"] if get_dry_run()         else []) +       \
               (["--yes"]     if get_non_interactive() else []) +       \
               list(args)

def install_pkgs(pkgs):
    if pkgs:
        execute_cmd(apt_get_cmd("install", *pkgs))
