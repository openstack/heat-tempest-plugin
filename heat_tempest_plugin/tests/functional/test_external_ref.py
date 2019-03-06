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

from heat_tempest_plugin.tests.functional import functional_base


class ExternalReferencesTest(functional_base.FunctionalTestsBase):

    TEMPLATE = '''
heat_template_version: 2016-10-14
resources:
  test1:
    type: OS::Heat::TestResource
'''
    TEMPLATE_WITH_EX_REF = '''
heat_template_version: 2016-10-14
resources:
  test1:
    type: OS::Heat::TestResource
    external_id: foobar
outputs:
  str:
    value: {get_resource: test1}
'''

    def _stack_create(self, template):
        self.stack_name = self._stack_rand_name()
        self.stack_identifier = self.stack_create(
            stack_name=self.stack_name,
            template=template,
            files={},
            disable_rollback=True,
            parameters={},
            environment={},
            expected_status='CREATE_COMPLETE'
        )

        expected_resources = {'test1': 'OS::Heat::TestResource'}
        self.assertEqual(expected_resources,
                         self.list_resources(self.stack_identifier))

    @decorators.idempotent_id('45449bad-18ba-4148-82e6-a6bc1e9a9b04')
    def test_create_with_external_ref(self):
        self._stack_create(self.TEMPLATE_WITH_EX_REF)
        stack = self.client.stacks.get(self.stack_identifier)
        self.assertEqual(
            [{'description': 'No description given',
              'output_key': 'str',
              'output_value': 'foobar'}], stack.outputs)

    @decorators.idempotent_id('fb16477c-e981-4ef9-a83b-c0acc162343a')
    def test_update_with_external_ref(self):
        self._stack_create(self.TEMPLATE)

        stack = self.client.stacks.get(self.stack_identifier)
        self.assertEqual([], stack.outputs)

        stack_name = self.stack_identifier.split('/')[0]
        kwargs = {'stack_id': self.stack_identifier, 'stack_name': stack_name,
                  'template': self.TEMPLATE_WITH_EX_REF, 'files': {},
                  'disable_rollback': True, 'parameters': {}, 'environment': {}
                  }
        self.client.stacks.update(**kwargs)
        self._wait_for_stack_status(self.stack_identifier, 'UPDATE_FAILED')

    @decorators.idempotent_id('0ac301c2-b377-49b8-82e2-2458634bc8cf')
    def test_update_stack_contain_external_ref(self):
        self._stack_create(self.TEMPLATE_WITH_EX_REF)

        stack = self.client.stacks.get(self.stack_identifier)
        self.assertEqual(
            [{'description': 'No description given',
              'output_key': 'str',
              'output_value': 'foobar'}], stack.outputs)

        # Update Stack without change external_id

        new_stack_name = self._stack_rand_name()
        kwargs = {'stack_id': self.stack_identifier,
                  'stack_name': new_stack_name,
                  'template': self.TEMPLATE_WITH_EX_REF, 'files': {},
                  'disable_rollback': True, 'parameters': {}, 'environment': {}
                  }
        self.client.stacks.update(**kwargs)

        self._wait_for_stack_status(self.stack_identifier, 'UPDATE_COMPLETE')

        expected_resources = {'test1': 'OS::Heat::TestResource'}
        self.assertEqual(expected_resources,
                         self.list_resources(self.stack_identifier))
