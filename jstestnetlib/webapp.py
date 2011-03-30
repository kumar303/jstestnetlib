
"""Utilities for controlling a web application under test."""

import os
import sys
import time
import socket
import tempfile
import signal
import subprocess
import time

import psutil


class IWebapp(object):
    """A web application under test.

    A class returned by a webapp factory should return an instance of
    something that implements this interface. See
    :class:`jstestnetlib.webapp.WebappServerCmd` for a concrete example.

    """

    def startup(self):
        """Start the webapp server subprocess."""
        raise NotImplementedError("This method must be implemented")

    def shutdown(self):
        """Shutdown the webapp server subprocess."""
        raise NotImplementedError("This method must be implemented")


class WebappServerCmd(IWebapp):
    """A subprocess that controls a server for a web application.
    """

    def __init__(self, cmd, logfile=None, **subproc_kwargs):

        self.cmd = cmd

        subproc_kwargs.setdefault('env', os.environ.copy())

        if not logfile:
            logfile = os.path.join(tempfile.gettempdir(),
                                   "jstestnetlib-webapp.log")
        self.logfile = logfile
        self.logfile_obj = None
        self.subproc_kwargs = subproc_kwargs
        self.proc = None

    def startup(self):
        """Start the webapp server subprocess."""
        self.logfile_obj = open(self.logfile, 'w')
        self.proc = subprocess.Popen(
                        self.cmd,
                        stdin=None,
                        stderr=self.logfile_obj.fileno(),
                        stdout=self.logfile_obj.fileno(),
                        **self.subproc_kwargs)
        time.sleep(2) # enough time to bind to local port, etc
        if self.proc.poll() != None:
            raise RuntimeError(
                "server terminated early (returncode: %s), probably due to "
                "an error.  Check the log for details: %s" % (
                                    self.proc.returncode, self.logfile))

    def shutdown(self):
        """Shutdown the webapp server subprocess."""
        if self.proc and self.proc.pid:
            kill_process_nicely(self.proc.pid)


def kill_process_nicely(pid):
    p = psutil.Process(pid)
    for child in p.get_children():
        kill_process_nicely(child.pid)
    p.send_signal(signal.SIGINT)
    p.wait(timeout=10)
