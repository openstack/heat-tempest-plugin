#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.lib import decorators

from heat_tempest_plugin.common import test
from heat_tempest_plugin.tests.scenario import scenario_base


@test.requires_resource_type('OS::Octavia::LoadBalancer')
class LoadBalancerTest(scenario_base.ScenarioTestsBase):
    def setUp(self):
        super(LoadBalancerTest, self).setUp()
        self.template_name = 'octavia_lbaas.yaml'
        self.member_template_name = 'lb_member.yaml'
        self.sub_dir = 'templates'

    def _create_stack(self):
        self.parameters = {
            'flavor': self.conf.minimal_instance_type,
            'image': self.conf.minimal_image_ref,
            'network': self.conf.fixed_network_name,
            'subnet': self.conf.fixed_subnet_name
        }
        member_template = self._load_template(
            __file__, self.member_template_name, self.sub_dir
        )
        self.files = {'lb_member.yaml': member_template}
        self.env = {'resource_registry': {
            'OS::Test::PoolMember': self.member_template_name}}

        return self.launch_stack(self.template_name,
                                 parameters=self.parameters,
                                 files=self.files,
                                 environment=self.env)

    @decorators.idempotent_id('5d2c4452-4433-4438-899c-7711c01d3c50')
    def test_create_update_loadbalancer(self):
        statuses = ['PENDING_UPDATE', 'ACTIVE']
        stack_identifier = self._create_stack()
        stack = self.client.stacks.get(stack_identifier)
        output = self._stack_output(stack, 'loadbalancer')
        self.assertIn(output['provisioning_status'], statuses)
        self.parameters['lb_algorithm'] = 'SOURCE_IP'

        self.update_stack(stack_identifier,
                          parameters=self.parameters,
                          existing=True)
        stack = self.client.stacks.get(stack_identifier)

        output = self._stack_output(stack, 'loadbalancer')
        self.assertIn(output['provisioning_status'], statuses)
        output = self._stack_output(stack, 'pool')
        self.assertEqual('SOURCE_IP', output['lb_algorithm'])

    @decorators.idempotent_id('970e91af-1be8-4990-837b-66f9b5aff2b9')
    def test_add_delete_poolmember(self):
        statuses = ['PENDING_UPDATE', 'ACTIVE']
        stack_identifier = self._create_stack()
        stack = self.client.stacks.get(stack_identifier)
        output = self._stack_output(stack, 'loadbalancer')
        self.assertIn(output['provisioning_status'], statuses)
        output = self._stack_output(stack, 'pool')
        self.assertEqual(1, len(output['members']))
        # add pool member
        self.parameters['member_count'] = 2
        self.update_stack(stack_identifier,
                          parameters=self.parameters,
                          existing=True)
        stack = self.client.stacks.get(stack_identifier)

        output = self._stack_output(stack, 'loadbalancer')
        self.assertIn(output['provisioning_status'], statuses)
        output = self._stack_output(stack, 'pool')
        self.assertEqual(2, len(output['members']))
        # delete pool member
        self.parameters['member_count'] = 1
        self.update_stack(stack_identifier,
                          parameters=self.parameters,
                          existing=True)
        stack = self.client.stacks.get(stack_identifier)

        output = self._stack_output(stack, 'loadbalancer')
        self.assertIn(output['provisioning_status'], statuses)
        output = self._stack_output(stack, 'pool')
        self.assertEqual(1, len(output['members']))
