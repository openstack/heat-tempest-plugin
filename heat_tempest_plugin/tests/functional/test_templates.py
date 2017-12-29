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


class TemplateAPITest(functional_base.FunctionalTestsBase):
    """This will test the following template calls:

    1. Get the template content for the specific stack
    2. List resource types
    3. Show resource details for OS::Heat::TestResource
    """

    template = {
        'heat_template_version': '2014-10-16',
        'description': 'Test Template APIs',
        'resources': {
            'test1': {
                'type': 'OS::Heat::TestResource',
                'properties': {
                    'update_replace': False,
                    'wait_secs': 0,
                    'value': 'Test1',
                    'fail': False,
                }
            }
        }
    }

    @decorators.idempotent_id('ac6ebc41-bd6a-4df4-80e5-f4b9ae3b5506')
    def test_get_stack_template(self):
        stack_identifier = self.stack_create(
            template=self.template
        )
        template_from_client = self.client.stacks.template(stack_identifier)
        self.assertEqual(self.template, template_from_client)

    @decorators.idempotent_id('9f9a2fc0-f029-4d1f-a2eb-f019b9f75944')
    def test_resource_types(self):
        resource_types = self.client.resource_types.list()
        self.assertTrue(any(resource.resource_type == "OS::Heat::TestResource"
                            for resource in resource_types))

    @decorators.idempotent_id('fafbdcd0-eec3-4e6f-9c88-1e4835d085cf')
    def test_show_resource_template(self):
        resource_details = self.client.resource_types.get(
            resource_type="OS::Heat::TestResource"
        )
        self.assertEqual("OS::Heat::TestResource",
                         resource_details['resource_type'])
