import os
import tempfile

import fudge
from nose.tools import eq_

from jstestnetlib.webapp import WebappServerCmd


@fudge.patch('jstestnetlib.webapp.subprocess',
             'jstestnetlib.webapp.kill_process_nicely')
def test_webapp_cmd(subprocess, kill_process_nicely):
    (subprocess.expects('Popen')
     .returns_fake().has_attr(returncode=0, pid=1234).provides('poll'))
    kill_process_nicely.expects_call().with_args(1234)

    webapp = WebappServerCmd(['python', 'manage.py', 'runserver'])
    eq_(webapp.logfile,
        os.path.join(tempfile.gettempdir(), "jstestnetlib-webapp.log"))
    webapp.startup()
    webapp.shutdown()
