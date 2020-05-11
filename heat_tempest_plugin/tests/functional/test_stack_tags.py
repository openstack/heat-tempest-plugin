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


class StackTagTest(functional_base.FunctionalTestsBase):

    template = '''
heat_template_version: 2014-10-16
description:
  foo
parameters:
  input:
    type: string
    default: test
resources:
  not-used:
    type: OS::Heat::TestResource
    properties:
      wait_secs: 1
      value: {get_param: input}
'''

    @decorators.idempotent_id('67332e51-b427-42d5-ad8d-fd2ec334f361')
    def test_stack_tag(self):
        # Stack create with stack tags
        tags = 'foo,bar'
        stack_identifier = self.stack_create(
            template=self.template,
            tags=tags
        )

        # Ensure property tag is populated and matches given tags
        stack = self.client.stacks.get(stack_identifier)
        self.assertEqual(['foo', 'bar'], stack.tags)

        # Update tags
        updated_tags = 'tag1,tag2'
        self.update_stack(
            stack_identifier,
            template=self.template,
            tags=updated_tags,
            parameters={'input': 'next'})

        # Ensure property tag is populated and matches updated tags
        updated_stack = self.client.stacks.get(stack_identifier)
        self.assertEqual(['tag1', 'tag2'], updated_stack.tags)

        # Delete tags
        self.update_stack(
            stack_identifier,
            template=self.template,
            parameters={'input': 'none'}
        )

        # Ensure property tag is not populated
        empty_tags_stack = self.client.stacks.get(stack_identifier)
        self.assertFalse(empty_tags_stack.tags)

    @decorators.idempotent_id('5ed79584-0684-4f9c-ae8e-44a8f874ec79')
    def test_hidden_stack(self):
        # Stack create with hidden stack tag
        tags = 'foo,%s' % self.conf.hidden_stack_tag
        self.stack_create(
            template=self.template,
            tags=tags)
        # Ensure stack does not exist when we do a stack list
        for stack in self.client.stacks.list():
            self.assertNotIn('hidden', stack.tags, "Hidden stack can be seen")
