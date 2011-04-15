
"""Remote control for a JS TestNet server."""
import json
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
        return self.request('GET', uri)

    def post(self, uri, data):
        return self.request('POST', uri, data=data)

    def request(self, method, uri, data=None):
        h = Http()
        if not uri.startswith('/'):
            uri = "/%s" % uri
        kwargs = {}
        if data:
            kwargs['body'] = urllib.urlencode(data)
        resp, content = h.request("%s%s" % (self.server, uri), method=method,
                                  **kwargs)
        if not resp['content-type'] == 'application/json':
            raise ConnectionError(
                    "Did not receive a JSON response: %r" % resp)
        resp_data = json.loads(content)
        if resp['status'] != '200':
            raise ConnectionError("[%s] %s" % (resp['status'],
                                               resp_data.get('message')))
        return resp_data

    def run_tests(self, test_suite, token, browsers, url=None):
        data = {'browsers': browsers, 'name': test_suite, 'token': token}
        if url:
            data.update(url=url)
        test = self.post('/start_tests/', data=data)
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
