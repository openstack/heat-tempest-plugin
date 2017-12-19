#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A test module to exercise the Heat API with gabbi.  """

import os
import unittest

from gabbi import driver
from six.moves.urllib import parse as urlparse
from tempest import config

from heat_tempest_plugin.common import test
from heat_tempest_plugin.services import clients

TESTS_DIR = 'gabbits'


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)

    conf = config.CONF.heat_plugin
    if conf.auth_url is None:
        # It's not configured, let's not load tests
        return
    manager = clients.ClientManager(conf)
    endpoint = manager.identity_client.get_endpoint_url(
        'orchestration', region=conf.region, endpoint_type=conf.endpoint_type)
    host = urlparse.urlparse(endpoint).hostname
    os.environ['OS_TOKEN'] = manager.identity_client.auth_token
    os.environ['PREFIX'] = test.rand_name('api')

    def register_test_case_id(test_case):
        tempest_id = test_case.test_data.get('desc')
        test_name = test_case.id()
        if not tempest_id:
            raise AssertionError(
                "No Tempest ID registered for API test %s" % test_name)

        def test_id():
            return test_name + '[id-%s]' % tempest_id

        test_case.id = test_id

    def register_test_suite_ids(test_suite):
        for test_case in test_suite:
            if isinstance(test_case, unittest.TestSuite):
                register_test_suite_ids(test_case)
            else:
                register_test_case_id(test_case)

    api_tests = driver.build_tests(test_dir, loader, host=host,
                                   url=endpoint, test_loader_name=__name__)
    register_test_suite_ids(api_tests)
    return api_tests
