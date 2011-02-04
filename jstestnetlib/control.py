
"""Remote control for a JS TestNet server."""
import json
import optparse
import time
import urllib

from httplib2 import Http


class ConnectionError(Exception):
    pass


class Connection(object):

    def __init__(self, server, wait_interval=1.0):
        if server.endswith('/'):
            server = server[0:-1]
        self.server = server
        self.wait_interval = wait_interval

    def get(self, uri):
        h = Http()
        if not uri.startswith('/'):
            uri = "/%s" % uri
        resp, content = h.request("%s%s" % (self.server, uri), 'GET')
        if not resp['content-type'] == 'application/json':
            raise ConnectionError(
                    "Did not receive a JSON response: %r" % resp)
        data = json.loads(content)
        if resp['status'] != '200':
            raise ConnectionError("[%s] %s" % (resp['status'],
                                               data.get('message')))
        return data

    def run_tests(self, test_suite, browsers):
        test = self.get('/start_tests/%s?browsers=%s' % (
                                    test_suite, urllib.quote(browsers)))
        results = []
        finished = False

        while not finished:
            server_result = self.get('/test/%s/result' % test['test_run_id'])
            finished = server_result['finished']
            time.sleep(self.wait_interval)

        # results = {u'worker_id': 7, u'user_agent': u'...',
        #            u'results': {u'tests': [
        #                           {u'test': u'Test passing',
        #                            u'message': u'some assertion...',
        #                            u'result': True,
        #                            u'module': u'Test Sessions'}...]}}
        return server_result


def main():
    p = optparse.OptionParser(usage='%prog [options] http://server-addr')
    p.add_option('-t', '--test', help='Name of test suite to run',
                 action='store')
    p.add_option('-l', '--list', help='List available test suites')
    (options, args) = p.parse_args()

    conn = Connection(args[0])
    if options.test:
        print conn.run_tests(options.test)
    else:
        raise NotImplementedError("option not suported yet")


if __name__ == '__main__':
    main()
