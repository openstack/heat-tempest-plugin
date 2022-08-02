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
import sys
import unittest

from gabbi import driver
import keystoneauth1
from oslo_log import log as logging
import six
from tempest import config

from heat_tempest_plugin.common import test
from heat_tempest_plugin.services import clients
from heat_tempest_plugin.tests.api import fixtures

LOG = logging.getLogger(__name__)
TESTS_DIR = 'gabbits'


def load_tests(loader, tests, pattern):
    """Provide a TestSuite to the discovery process."""
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)

    endpoint = None
    conf = config.CONF.heat_plugin
    if conf.auth_url:
        try:
            manager = clients.ClientManager(conf)
            endpoint = manager.identity_client.get_endpoint_url(
                'orchestration', region=conf.region,
                endpoint_type=conf.endpoint_type)
            os.environ['PREFIX'] = test.rand_name('api')

        # Catch the authentication exceptions that can happen if one of the
        # following conditions occur:
        #   1. conf.auth_url IP/port is incorrect or keystone not available
        #      (ConnectFailure)
        #   2. conf.auth_url is malformed (BadRequest, UnknownConnectionError,
        #      EndpointNotFound, NotFound, or DiscoveryFailure)
        #   3. conf.username/password is incorrect (Unauthorized)
        #   4. conf.project_name is missing/incorrect (EmptyCatalog)
        # These exceptions should not prevent a test list from being returned,
        # so just issue a warning log and move forward with test listing.
        except (keystoneauth1.exceptions.http.BadRequest,
                keystoneauth1.exceptions.http.Unauthorized,
                keystoneauth1.exceptions.http.NotFound,
                keystoneauth1.exceptions.catalog.EmptyCatalog,
                keystoneauth1.exceptions.catalog.EndpointNotFound,
                keystoneauth1.exceptions.discovery.DiscoveryFailure,
                keystoneauth1.exceptions.connection.UnknownConnectionError,
                keystoneauth1.exceptions.connection.ConnectFailure):
            LOG.warning("Keystone auth exception: %s: %s" %
                        (sys.exc_info()[0], sys.exc_info()[1]))
            # Clear the auth_url, as there is no point in tempest trying
            # to authenticate later with mis-configured or unreachable endpoint
            conf.auth_url = None

        except Exception:
            LOG.error("Fatal exception: %s: %s" % (sys.exc_info()[0],
                                                   sys.exc_info()[1]))
            raise

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

    cert_validate = not conf.disable_ssl_certificate_validation
    try:
        api_tests = driver.build_tests(test_dir, loader, url=endpoint, host="",
                                       fixture_module=fixtures,
                                       cert_validate=cert_validate,
                                       test_loader_name=__name__)
    except TypeError as ex:
        err_msg = "got an unexpected keyword argument 'cert_validate'"
        if err_msg in six.text_type(ex):
            api_tests = driver.build_tests(test_dir, loader,
                                           url=endpoint, host="",
                                           fixture_module=fixtures,
                                           test_loader_name=__name__)
        else:
            raise

    register_test_suite_ids(api_tests)
    return api_tests
