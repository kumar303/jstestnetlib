
import logging
import os
import unittest

from nose.plugins import Plugin

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
        parser.add_option('--jstests-browsers', action="store",
                          help=('Comma separated list of browsers to run '
                                'tests against, see JS TestNet docs for '
                                'details. Example: '
                                'firefox=~3,firefox=~4,chrome'))
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
        self.started = False
        self.conn = Connection(self.options.jstests_server)

    def loadTestsFromDir(self, directory):
        if self.started:
            # hijacking loadTestsFromDir to run tests once
            # and only once.
            return
        self.started = True
        log.debug('Starting %r [%s] %s' % (self.options.jstests_suite,
                                           self.options.jstests_server,
                                           self.options.jstests_browsers))

        tests = self.conn.run_tests(self.options.jstests_suite,
                                    self.options.jstests_browsers)
        for test in tests['results']:
            successful = True
            # TODO(Kumar) find a way to not parse results twice.
            for assertion in test['assertions']:
                if not assertion['result']:
                    successful = False
                    break
            yield JSTestCase(test)
            if self.result.shouldStop and not self.successful:
                break

    def prepareTestResult(self, result):
        self.result = result


class JSTestError(Exception):
    pass


class JSTestCase(unittest.TestCase):
    """A test case that represents a remote test known by the server."""
    __test__ = False # this is not a collectible test

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
                    traceback = None # Python
                    # TODO(Kumar) add shortened worker_user_agent here?
                    e = (JSTestError, "%s on <%s>{%s} %s" % (
                         msg,
                         assertion['browser'],
                         assertion['worker_id'],
                         assertion['stacktrace'] or ''), traceback)
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
