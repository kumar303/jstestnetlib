
import logging
import os
import unittest

from nose.plugins import Plugin

from jstestnetlib import webapp
from jstestnetlib.control import Connection

log = logging.getLogger('nose.plugins.jstests')


class JSTests(Plugin):
    """Run JavaScript tests using a JS TestNet server."""
    name = 'jstests'

    def options(self, parser, env=os.environ):
        super(JSTests, self).options(parser, env=env)
        parser.add_option('--jstests-server', action="store",
                          help='http://jstestnet-server/')
        parser.add_option('--jstests-suite', action="store",
                          help='Name of test suite to run')
        parser.add_option('--jstests-url', action="store",
                          help='URL of the QUnit test suite')
        parser.add_option('--jstests-token', action="store",
                          help='Security token to start this test suite')
        parser.add_option('--jstests-browsers', action="store",
                          help=('Comma separated list of browsers to run '
                                'tests against, see JS TestNet docs for '
                                'details. Example: '
                                'firefox=~3,firefox=~4,chrome'))
        parser.add_option('--jstests-restart', action="store_true",
                          help=('Restarts all browser workers '
                                'before running tests.'))
        self.parser = parser

    def configure(self, options, conf):
        super(JSTests, self).configure(options, conf)
        if not self.enabled:
            return
        self.options = options
        if not self.options.jstests_server:
            self.parser.error("Missing --jstests-server")
        if not self.options.jstests_suite:
            self.parser.error("Missing --jstests-suite")
        if not self.options.jstests_browsers:
            self.parser.error("Missing --jstests-browsers")
        if not self.options.jstests_token:
            self.parser.error("Missing --jstests-token")
        self.started = False
        self.conn = Connection(self.options.jstests_server)

    def loadTestsFromDir(self, directory):
        if self.started:
            # hijacking loadTestsFromDir to run tests once
            # and only once.
            return
        self.started = True
        if self.options.jstests_restart:
            resp = self.conn.get('/restart_workers')
            log.debug('Restarted %s worker(s)' % resp['workers_restarted'])
        log.debug('Starting %r [%s] %s' % (self.options.jstests_suite,
                                           self.options.jstests_server,
                                           self.options.jstests_browsers))

        tests = self.conn.run_tests(self.options.jstests_suite,
                                    self.options.jstests_token,
                                    self.options.jstests_browsers,
                                    self.options.jstests_url)
        for test in tests['results']:
            successful = True
            # TODO(Kumar) find a way to not parse results twice.
            for assertion in test['assertions']:
                if not assertion['result']:
                    successful = False
                    break
            yield JSTestCase(test)
            if self.result.shouldStop and not successful:
                break

    def prepareTestResult(self, result):
        self.result = result


class JSTestError(Exception):
    pass


class JSTestCase(unittest.TestCase):
    """A test case that represents a remote test known by the server."""
    __test__ = False  # this is not a collectible test

    def __init__(self, test):
        self.test = test
        super(JSTestCase, self).__init__()

    def runTest(self):
        pass

    def run(self, result):
        result.startTest(self)
        try:
            passed = True
            # Since unittest does not log assertions,
            # iterate until the first failure (if there is one).
            for assertion in self.test['assertions']:
                if not assertion['result']:
                    passed = False
                    # log.debug(repr(self.test))
                    msg = assertion['message'] or '<unknown error>'
                    traceback = None  # Python
                    # TODO(Kumar) add shortened worker_user_agent here?
                    e = (JSTestError, "%s on <%s>{%s} %s" % (
                         msg,
                         assertion['browser'],
                         assertion['worker_id'],
                         assertion.get('stacktrace') or ''), traceback)
                    result.addError(self, e)
                    break
            if passed:
                result.addSuccess(self)
        finally:
            result.stopTest(self)

    def address(self):
        return (self.id(), None, None)

    def id(self):
        return repr(self)

    def shortDescription(self):
        return "%r: %s: %s" % (self, self.test['module'], self.test['test'])

    def __repr__(self):
        return "JS"

    __str__ = __repr__


class DjangoServPlugin(Plugin):
    """Starts/stops Django runserver for tests."""
    name = 'django-serv'
    score = 99

    def __init__(self, root=None):
        self.root = root
        super(DjangoServPlugin, self).__init__()

    def options(self, parser, env=os.environ):
        super(DjangoServPlugin, self).options(parser, env=env)
        cwd = os.path.abspath(os.getcwd())
        parser.add_option('--django-root-dir', default=cwd,
                          help='Root directory of the django project (where '
                               'manage.py is). Default: %default')
        parser.add_option('--django-host', default='0.0.0.0',
                          help='Hostname or IP address to bind manage.py '
                               'runserver to. This must match the host/ip '
                               'configured in your --jstests-suite default '
                               'URL or passed in --jstests-url.'
                               'Default: %default')
        parser.add_option('--django-port', default=9877,
                          help='Port to bind manage.py runserver to. '
                               'This must match the port '
                               'configured in your --jstests-suite default '
                               'URL or passed in --jstests-url.'
                               'Default: %default')
        parser.add_option('--django-log', default=None,
                          help='Log filename for the manage.py runserver '
                               'command. Logs to a temp file by default.')
        parser.add_option('--django-startup-uri', default='/',
                          help='URI for checking that the server '
                               'started up okay. Default: GET %default')
        self.parser = parser

    def configure(self, options, conf):
        super(DjangoServPlugin, self).configure(options, conf)
        if not self.enabled:
            return
        self.options = options
        if self.options.django_root_dir:
            self.root = self.options.django_root_dir
        assert 'manage.py' in os.listdir(self.root), (
            'Expected this to be the root dir containing manage.py: %s' %
            self.root)

    def begin(self):
        bind = '%s:%s' % (self.options.django_host,
                          self.options.django_port)
        startup_url = 'http://%s%s' % (bind, self.options.django_startup_uri)
        self.django_app = webapp.WebappServerCmd(
                                ['python', 'manage.py', 'runserver', bind,
                                 '--noreload'],
                                startup_url, logfile=self.options.django_log,
                                cwd=self.root)
        self.django_app.startup()

    def finalize(self, result):
        self.django_app.shutdown()
