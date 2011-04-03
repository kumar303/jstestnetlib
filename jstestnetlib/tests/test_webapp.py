import os
import tempfile

import fudge
from fudge.inspector import arg
from nose.tools import eq_

from jstestnetlib.webapp import WebappServerCmd


@fudge.patch('jstestnetlib.webapp.subprocess',
             'jstestnetlib.webapp.kill_process_nicely',
             'time.sleep')
def test_webapp_cmd(subprocess, kill_process_nicely, sleep):
    (subprocess.expects('Popen')
     .returns_fake().has_attr(returncode=0, pid=1234).provides('poll'))
    kill_process_nicely.expects_call().with_args(1234)
    sleep.is_a_stub()

    webapp = WebappServerCmd(['python', 'manage.py', 'runserver'])
    eq_(webapp.logfile,
        os.path.join(tempfile.gettempdir(), "jstestnetlib-webapp.log"))
    webapp.startup()
    webapp.shutdown()


@fudge.patch('jstestnetlib.webapp.subprocess',
             'jstestnetlib.webapp.kill_process_nicely',
             'time.sleep',
             '__builtin__.open')
def test_custom_logfile(subprocess, kill_process_nicely, sleep, open):
    (subprocess.expects('Popen')
     .returns_fake().has_attr(returncode=0, pid=1234).provides('poll'))
    kill_process_nicely.is_a_stub()
    sleep.is_a_stub()
    (open.expects_call().with_args('/custom.log', 'w')
     .returns_fake().is_a_stub())

    webapp = WebappServerCmd(['python', 'manage.py', 'runserver'],
                             logfile='/custom.log')
    webapp.startup()
