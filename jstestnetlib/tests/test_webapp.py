import os
import tempfile
import urllib2

import fudge
from fudge.inspector import arg
from nose.tools import eq_, raises

from jstestnetlib.webapp import WebappServerCmd


@fudge.patch('jstestnetlib.webapp.subprocess',
             'jstestnetlib.webapp.kill_process_nicely',
             'time.sleep',
             'jstestnetlib.webapp.urllib2.urlopen')
def test_webapp_cmd(subprocess, kill_process_nicely, sleep, urlopen):
    (subprocess.expects('Popen')
     .returns_fake().has_attr(returncode=0, pid=1234).provides('poll'))
    kill_process_nicely.expects_call().with_args(1234)
    sleep.is_a_stub()
    (urlopen.expects_call().with_args('http://localhost:8000/')
     .returns_fake().expects('close'))

    webapp = WebappServerCmd(['python', 'manage.py', 'runserver'],
                             'http://localhost:8000/')
    eq_(webapp.logfile,
        os.path.join(tempfile.gettempdir(), "jstestnetlib-webapp.log"))
    webapp.startup()
    webapp.shutdown()


@fudge.patch('jstestnetlib.webapp.subprocess',
             'jstestnetlib.webapp.kill_process_nicely',
             'time.sleep',
             'jstestnetlib.webapp.urllib2.urlopen',
             '__builtin__.open')
def test_custom_logfile(subprocess, kill_process_nicely, sleep,
                        urlopen, open):
    (subprocess.expects('Popen')
     .returns_fake().has_attr(returncode=0, pid=1234).provides('poll'))
    kill_process_nicely.is_a_stub()
    sleep.is_a_stub()
    urlopen.is_a_stub()
    (open.expects_call().with_args('/custom.log', 'w')
     .returns_fake().is_a_stub())

    webapp = WebappServerCmd(['python', 'manage.py', 'runserver'],
                             'http://localhost:8000/',
                             logfile='/custom.log')
    webapp.startup()


@raises(RuntimeError)
@fudge.patch('jstestnetlib.webapp.subprocess',
             'jstestnetlib.webapp.kill_process_nicely',
             'time.sleep',
             'jstestnetlib.webapp.urllib2.urlopen')
def test_timeout(subprocess, kill_process_nicely, sleep, urlopen):
    (subprocess.expects('Popen')
     .returns_fake().has_attr(returncode=0, pid=1234).provides('poll'))
    kill_process_nicely.is_a_stub()
    sleep.is_a_stub()
    urlopen.expects_call().raises(urllib2.URLError('could not access server'))

    webapp = WebappServerCmd(['python', 'manage.py', 'runserver'],
                             'http://localhost:8000/')
    webapp.startup()
