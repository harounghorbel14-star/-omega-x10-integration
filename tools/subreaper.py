"""Run a command as a child subreaper that reaps orphaned zombies (what tini / docker --init provide).

  python3 tools/subreaper.py <command> [args...]

This sandbox's PID 1 does not reap orphans, so a killed grandchild stays a zombie and tests that
probe it with kill(pid, 0) see it as alive. As a subreaper, orphans are re-parented to this process
and reaped here. Exits with the command's status as soon as the command itself exits; descendants
still running at that point (e.g. daemons a test suite leaves behind) are not waited for.
"""
import ctypes
import os
import sys

PR_SET_CHILD_SUBREAPER = 36
if ctypes.CDLL(None, use_errno=True).prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
    sys.exit("prctl(PR_SET_CHILD_SUBREAPER) failed")
main = os.fork()
if main == 0:
    os.execvp(sys.argv[1], sys.argv[1:])
status = 1
while True:
    try:
        pid, st = os.waitpid(-1, 0)
    except ChildProcessError:
        break
    if pid == main:
        status = os.waitstatus_to_exitcode(st)
        # reap zombies that are already pending, then stop waiting for live descendants
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
        break
sys.exit(status)
