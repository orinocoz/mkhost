import datetime
import functools
import io
import logging
import os
import subprocess
import sys
import threading
import time

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
# Common variables
##############################################################################

_subproc_running = False

##############################################################################
# Common functions
##############################################################################

# Continuously reads from the given stream and notifies the given handlers.
# Returns when _subproc_running becomes false.
def _stream_reader(lk, stream, handlers):
    while True:
        chunk = stream.read(1)
        if chunk:
            with lk:
                for h in handlers:
                    h(chunk)
        else:
            with lk:
                if not _subproc_running:
                    break
            time.sleep(1)

    with lk:
        # logging.debug("_stream_reader return")
        stream.close()

# Writes the given string (chunk) to the given stream; flushes the stream.
def _stream_writer(stream, chunk):
    stream.write(chunk)
    stream.flush()

# Executes a system command in an interactive way.
# cmdline must be a list.
# Returns a pair: (stdout lines, stderr lines).
def execute_cmd_interactive(cmdline):
    global _subproc_running
    logging.info(" ".join(cmdline))

    # start the child process
    proc = subprocess.Popen(
               cmdline,
               bufsize=-1,
               close_fds=True,
               shell=False,
               stdin=sys.stdin,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               universal_newlines=True)

    # shared lock + flag
    lk = threading.Lock()
    _subproc_running = True

    # stdout
    out_buffer = io.StringIO()
    out_reader = threading.Thread(target=_stream_reader, name='stdout reader', daemon=True,
                     args=(lk, proc.stdout, [functools.partial(_stream_writer, sys.stdout), out_buffer.write]))
    # stderr
    err_buffer = io.StringIO()
    err_reader = threading.Thread(target=_stream_reader, name='stderr reader', daemon=True,
                     args=(lk, proc.stderr, [functools.partial(_stream_writer, sys.stderr), err_buffer.write]))

    # start the threads
    for t in (err_reader, out_reader):
        t.start()

    # wait for the process to terminate
    proc.wait()
    with lk:
        _subproc_running = False

    # join the reader threads
    for t in (err_reader, out_reader):
        t.join()

    # check the return code
    if proc.returncode:
        raise subprocess.CalledProcessError(returncode=proc.returncode, cmd=" ".join(cmdline))

    out_lines = (out_buffer.getvalue() or '').splitlines()
    err_lines = (err_buffer.getvalue() or '').splitlines()
    # logging.debug("out_lines: {}".format(out_lines))
    return (out_lines, err_lines)

# Executes a system command in a non-interactive way (batch).
# cmdline must be a list.
# Returns a pair: (stdout lines, stderr lines).
def execute_cmd_batch(cmdline, input=None):
    logging.info(" ".join(cmdline))

    proc_result = subprocess.run(
                        cmdline,
                        shell=False,
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
    return (out_lines, err_lines)

# Executes a system command.
# cmdline must be a list.
# Returns a pair: (stdout lines, stderr lines).
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

def update_pkgs():
    if not get_dry_run():
        execute_cmd(apt_get_cmd("update"))
        execute_cmd(apt_get_cmd("upgrade"))

def install_pkgs(pkgs):
    if pkgs:
        execute_cmd(apt_get_cmd("install", *pkgs))
