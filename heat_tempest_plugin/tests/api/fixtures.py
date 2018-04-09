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

import os

from gabbi import fixture
from heat_tempest_plugin.services import clients
from tempest import config


class AuthenticationFixture(fixture.GabbiFixture):
    def start_fixture(self):
        conf = config.CONF.heat_plugin
        manager = clients.ClientManager(conf)
        os.environ['OS_TOKEN'] = manager.identity_client.auth_token

    def stop_fixture(self):
        pass
