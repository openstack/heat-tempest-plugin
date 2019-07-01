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

import six
import uuid

from heat_tempest_plugin.tests.scenario import scenario_base
from tempest.lib import decorators


class RemoteDeeplyNestedStackTest(scenario_base.ScenarioTestsBase):
    @decorators.idempotent_id('2ed94cae-da14-4060-a6b3-526e7a8cbbe4')
    def test_remote_nested(self):
        parameters = {
            'name': 'remote-nested',
            'network_name': self.conf.floating_network_name,
        }

        stack_id = self.launch_stack(
            template_name='remote_nested_root.yaml',
            parameters={'region': self.conf.region},
            environment={'parameters': parameters}
        )

        stack = self.client.stacks.get(stack_id)
        router_id = self._stack_output(stack, 'router')
        self.assertIsInstance(router_id, six.string_types)
        uuid.UUID(router_id)

        self._stack_delete(stack_id)
