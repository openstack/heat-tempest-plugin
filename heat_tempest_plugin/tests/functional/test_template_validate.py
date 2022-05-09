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


from heatclient import exc
from tempest.lib import decorators

from heat_tempest_plugin.tests.functional import functional_base


class StackTemplateValidateTest(functional_base.FunctionalTestsBase):

    random_template = '''
heat_template_version: 2014-10-16
description: the stack description
parameters:
  aparam:
    type: number
    default: 10
    description: the param description
resources:
  myres:
    type: OS::Heat::RandomString
    properties:
      length: {get_param: aparam}
'''

    parent_template = '''
heat_template_version: 2014-10-16
description: the parent template
parameters:
  pparam:
    type: number
    default: 5
    description: the param description
resources:
  nres:
    type: mynested.yaml
    properties:
      aparam: {get_param: pparam}
'''

    parent_template_noprop = '''
heat_template_version: 2014-10-16
description: the parent template
resources:
  nres:
    type: mynested.yaml
'''

    random_template_groups = '''
heat_template_version: 2014-10-16
description: the stack description
parameters:
  aparam:
    type: number
    default: 10
    description: the param description
  bparam:
    type: string
    default: foo
  cparam:
    type: string
    default: secret
    hidden: true
parameter_groups:
- label: str_params
  description: The string params
  parameters:
  - bparam
  - cparam
resources:
  myres:
    type: OS::Heat::RandomString
    properties:
      length: {get_param: aparam}
'''

    @decorators.idempotent_id('b65a80c2-a507-4deb-9e7e-43181cc05211')
    def test_template_validate_basic(self):
        ret = self.client.stacks.validate(template=self.random_template)
        expected = {'Description': 'the stack description',
                    'Parameters': {
                        'aparam': {'Default': 10,
                                   'Description': 'the param description',
                                   'Label': 'aparam',
                                   'NoEcho': 'false',
                                   'Type': 'Number'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('bf27371d-e202-4bae-9f13-2ef137958517')
    def test_template_validate_override_default(self):
        env = {'parameters': {'aparam': 5}}
        ret = self.client.stacks.validate(template=self.random_template,
                                          environment=env)
        expected = {'Description': 'the stack description',
                    'Parameters': {
                        'aparam': {'Default': 10,
                                   'Value': 5,
                                   'Description': 'the param description',
                                   'Label': 'aparam',
                                   'NoEcho': 'false',
                                   'Type': 'Number'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {'aparam': 5},
                        'resource_registry': {u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('0278e03d-ed50-4909-b29d-9c4267d3fcd6')
    def test_template_validate_override_none(self):
        env = {'resource_registry': {
               'OS::Heat::RandomString': 'OS::Heat::None'}}
        ret = self.client.stacks.validate(template=self.random_template,
                                          environment=env)
        expected = {'Description': 'the stack description',
                    'Parameters': {
                        'aparam': {'Default': 10,
                                   'Description': 'the param description',
                                   'Label': 'aparam',
                                   'NoEcho': 'false',
                                   'Type': 'Number'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {
                            'OS::Heat::RandomString': 'OS::Heat::None',
                            u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('acb1435b-f1db-4427-9121-7e3144ddb81e')
    def test_template_validate_basic_required_param(self):
        tmpl = self.random_template.replace('default: 10', '')
        ret = self.client.stacks.validate(template=tmpl)
        expected = {'Description': 'the stack description',
                    'Parameters': {
                        'aparam': {'Description': 'the param description',
                                   'Label': 'aparam',
                                   'NoEcho': 'false',
                                   'Type': 'Number'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('7aac1feb-8256-4f70-8459-5e9780d28904')
    def test_template_validate_fail_version(self):
        fail_template = self.random_template.replace('2014-10-16', 'invalid')
        ex = self.assertRaises(exc.HTTPBadRequest,
                               self.client.stacks.validate,
                               template=fail_template)
        self.assertIn('The template version is invalid', str(ex))

    @decorators.idempotent_id('6a6472d2-71fa-4ebe-a2b6-20878838555b')
    def test_template_validate_parameter_groups(self):
        ret = self.client.stacks.validate(template=self.random_template_groups)
        expected = {'Description': 'the stack description',
                    'ParameterGroups':
                    [{'description': 'The string params',
                      'label': 'str_params',
                      'parameters': ['bparam', 'cparam']}],
                    'Parameters':
                    {'aparam':
                     {'Default': 10,
                      'Description': 'the param description',
                      'Label': 'aparam',
                      'NoEcho': 'false',
                      'Type': 'Number'},
                     'bparam':
                     {'Default': 'foo',
                      'Description': '',
                      'Label': 'bparam',
                      'NoEcho': 'false',
                      'Type': 'String'},
                     'cparam':
                     {'Default': 'secret',
                      'Description': '',
                      'Label': 'cparam',
                      'NoEcho': 'true',
                      'Type': 'String'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('5100cf18-f52a-47a2-880c-d540edad149f')
    def test_template_validate_nested_off(self):
        files = {'mynested.yaml': self.random_template}
        ret = self.client.stacks.validate(template=self.parent_template,
                                          files=files)
        expected = {'Description': 'the parent template',
                    'Parameters': {
                        'pparam': {'Default': 5,
                                   'Description': 'the param description',
                                   'Label': 'pparam',
                                   'NoEcho': 'false',
                                   'Type': 'Number'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {
                            u'mynested.yaml': u'mynested.yaml',
                            u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('480bcf64-25ae-49c7-b147-7cbc27d09cea')
    def test_template_validate_nested_on(self):
        files = {'mynested.yaml': self.random_template}
        ret = self.client.stacks.validate(template=self.parent_template_noprop,
                                          files=files,
                                          show_nested=True)
        expected = {'Description': 'the parent template',
                    'Parameters': {},
                    'NestedParameters': {
                        'nres': {'Description': 'the stack description',
                                 'Parameters': {'aparam': {'Default': 10,
                                                           'Description':
                                                           'the param '
                                                           'description',
                                                           'Label': 'aparam',
                                                           'NoEcho': 'false',
                                                           'Type': 'Number'}},
                                 'Type': 'mynested.yaml'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {
                            u'mynested.yaml': u'mynested.yaml',
                            u'resources': {}}}}
        self.assertEqual(expected, ret)

    @decorators.idempotent_id('a0bb07f0-2e10-4226-a205-a7eb04df415f')
    def test_template_validate_nested_on_multiple(self):
        # parent_template -> nested_template -> random_template
        nested_template = self.random_template.replace(
            'OS::Heat::RandomString', 'mynested2.yaml')
        files = {'mynested.yaml': nested_template,
                 'mynested2.yaml': self.random_template}
        ret = self.client.stacks.validate(template=self.parent_template,
                                          files=files,
                                          show_nested=True)

        n_param2 = {'myres': {'Description': 'the stack description',
                              'Parameters': {'aparam': {'Default': 10,
                                                        'Description':
                                                        'the param '
                                                        'description',
                                                        'Label': 'aparam',
                                                        'NoEcho': 'false',
                                                        'Type': 'Number'}},
                              'Type': 'mynested2.yaml'}}
        expected = {'Description': 'the parent template',
                    'Parameters': {
                        'pparam': {'Default': 5,
                                   'Description': 'the param description',
                                   'Label': 'pparam',
                                   'NoEcho': 'false',
                                   'Type': 'Number'}},
                    'NestedParameters': {
                        'nres': {'Description': 'the stack description',
                                 'Parameters': {'aparam': {'Default': 10,
                                                           'Description':
                                                           'the param '
                                                           'description',
                                                           'Label': 'aparam',
                                                           'Value': 5,
                                                           'NoEcho': 'false',
                                                           'Type': 'Number'}},
                                 'NestedParameters': n_param2,
                                 'Type': 'mynested.yaml'}},
                    'Environment': {
                        'event_sinks': [],
                        'parameter_defaults': {},
                        'parameters': {},
                        'resource_registry': {
                            u'mynested.yaml': u'mynested.yaml',
                            'resources': {}}}}
        self.assertEqual(expected, ret)
