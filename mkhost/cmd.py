import io
import logging
import subprocess
import threading
import time

import mkhost.common

##############################################################################
# global variables
##############################################################################

_subproc_running = False

##############################################################################
# interactive and non-interactive system command execution functions
# with stdout/stderr extraction and error propagation.
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
        stream.close()

# Writes the given string (chunk) to the given stream; flushes the stream.
def _stream_writer(stream, chunk):
    stream.write(chunk)
    stream.flush()

# Extracts and optionally prints the error/output lines captured in the
# process call.
# Returns a pair: (stdout lines, stderr lines).
def _extract_err_out_lines(proc_result, print_err=True, print_out=True):
    err_lines = (proc_result.stderr or '').splitlines()
    out_lines = (proc_result.stdout or '').splitlines()

    if print_err:
        for x in err_lines:
            logging.warning(x)

    if print_out:
        for x in out_lines:
            logging.debug(x)

    return (out_lines, err_lines)

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
    out_reader = threading.Thread(target=_stream_reader, name='stdout-reader', daemon=True,
                     args=(lk, proc.stdout, [functools.partial(_stream_writer, sys.stdout), out_buffer.write]))
    # stderr
    err_buffer = io.StringIO()
    err_reader = threading.Thread(target=_stream_reader, name='stderr-reader', daemon=True,
                     args=(lk, proc.stderr, [functools.partial(_stream_writer, sys.stderr), err_buffer.write]))

    # start the threads
    for t in (err_reader, out_reader):
        t.start()

    # wait for the child process to terminate
    proc.wait()
    with lk:
        _subproc_running = False

    # join the reader threads
    for t in (err_reader, out_reader):
        t.join()

    # check the child process return code
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

    try:
        proc_result = subprocess.run(
                            cmdline,
                            shell=False,
                            input=input,
                            capture_output=True,
                            check=True,
                            universal_newlines=True)

        return _extract_err_out_lines(proc_result)
    except subprocess.CalledProcessError as e:
        _extract_err_out_lines(e)
        raise e

# Executes a system command.
# cmdline must be a list.
# Returns a pair: (stdout lines, stderr lines).
def execute_cmd(cmdline):
    if mkhost.common.get_non_interactive():
        return execute_cmd_batch(cmdline)
    else:
        return execute_cmd_interactive(cmdline)
