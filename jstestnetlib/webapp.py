
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
    :class:`ui_tester.webapp.WebappServerCmd` for a concrete example.

    Required attributes:

    **server_ip_addr**
        IP address of the web application (for remote testing)

    **server_port**
        Network port of the web application

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

    def __init__(self, cmd, server_ip_addr=None, server_port=None,
                       logfile=None, **subproc_kwargs):

        self.cmd = cmd

        subproc_kwargs.setdefault('env', os.environ.copy())

        if not logfile:
            logfile = os.path.join(tempfile.gettempdir(),
                                   "jstestnetlib-webapp.log")
        self.logfile = logfile
        self.logfile_obj = None
        self.subproc_kwargs = subproc_kwargs
        self.proc = None
        self.server_ip_addr = server_ip_addr or self._get_server_ip_addr()
        self.server_port = server_port
        if not self.server_port:
            raise ValueError("server_port= of this webapp was not set")

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

    def _get_server_ip_addr(self):
        """Get externally accessible local IP of the web app under test,
        which is assumed to be running on this machine, so that remote VM can
        connect to the app.
        """
        remote = ("mozilla.com", 80)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(remote)
            ip, localport = s.getsockname()
            s.close()
        except socket.gaierror:
            # no Internet, assume its running on localhost
            ip = "127.0.0.1"
        return ip


def kill_process_nicely(pid):
    p = psutil.Process(pid)
    for child in p.get_children():
        kill_process_nicely(child.pid)
    p.send_signal(signal.SIGINT)
    p.wait(timeout=10)
