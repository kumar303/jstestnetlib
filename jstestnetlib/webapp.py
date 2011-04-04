
"""Utilities for controlling a web application under test."""

import os
import sys
import time
import socket
import tempfile
import signal
import subprocess
import time
import urllib2

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

    **cmd**
        list of commands to run (as accepted by subprocess.Popen)
    **startup_url**
        A URL that can be opened to verify that the server started up
        corectly. Example: http://localhost:8000/
    **logfile**
        Path to the webapp's log. When None, a temp file will be created.

    All other keyword arguments are passed through to subprocess.Popen
    """

    def __init__(self, cmd, startup_url, logfile=None, **subproc_kwargs):

        self.cmd = cmd
        self.startup_url = startup_url

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
        wait = 1
        time_taken = 0
        timeout = 10
        # Wait for webapp to bind to socket
        while 1:
            time.sleep(wait)
            try:
                f = urllib2.urlopen(self.startup_url)
            except urllib2.URLError, exc:
                time_taken += wait
                if time_taken >= timeout:
                    raise RuntimeError(
                        'The server did not start up within %s seconds. '
                        'See log %r for details. (Checked with URL: %s; '
                        'last exception: %s: %s)' % (
                                        timeout, self.logfile,
                                        self.startup_url,
                                        exc.__class__.__name__, exc))
            else:
                f.close()
                break

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
