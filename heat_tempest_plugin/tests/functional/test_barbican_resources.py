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
from heat_tempest_plugin.tests.functional import functional_base


# Barbican objects are immutable, so a stack update that changes a value
# REPLACES the resource (Heat creates the new object and deletes the old).
# The test verifies the replace: after an update the *_ref outputs change.

barbican_template = '''
heat_template_version: 2021-04-16
description: >
  Exercise the full create/update/delete lifecycle of the Barbican
  resources: OS::Barbican::Secret, OS::Barbican::GenericContainer
  (referencing a secret) and OS::Barbican::Order.
parameters:
  payload:
    type: string
    default: s3cr3t-payload-v1
  bit_length:
    type: number
    default: 256
resources:
  my_secret:
    type: OS::Barbican::Secret
    properties:
      name: heat-secret-opaque
      payload: { get_param: payload }
      payload_content_type: text/plain
      secret_type: opaque
  my_container:
    type: OS::Barbican::GenericContainer
    properties:
      name: heat-generic-container
      secrets:
        - name: secret_a
          ref: { get_resource: my_secret }
  my_key_order:
    type: OS::Barbican::Order
    properties:
      name: heat-key-order
      type: key
      algorithm: aes
      bit_length: { get_param: bit_length }
      mode: cbc
  my_order_container:
    type: OS::Barbican::GenericContainer
    properties:
      name: heat-container-order-secret
      secrets:
        - name: order_secret
          ref: { get_attr: [my_key_order, secret_ref] }
outputs:
  secret_ref:
    value: { get_resource: my_secret }
  container_ref:
    value: { get_resource: my_container }
  order_ref:
    value: { get_resource: my_key_order }
  order_secret_ref:
    value: { get_attr: [my_key_order, secret_ref] }
  order_container_ref:
    value: { get_resource: my_order_container }
'''


@test.requires_service('barbican')
class BarbicanResourcesTest(functional_base.FunctionalTestsBase):
    """OS::Barbican::* lifecycle as admin; order delete is role:admin."""

    def setUp(self):
        super(BarbicanResourcesTest, self).setUp()
        if not self.conf.admin_username or not self.conf.admin_password:
            self.skipTest('No admin creds found, skipping')
        # Own the stack as admin so the Barbican resource deletes (notably
        # the order, admin-only under legacy policy) succeed.
        # TODO(ramishra): use a normal user once we stop gating older branches
        self.setup_clients_for_admin()

    @decorators.idempotent_id('9a53e9f1-3f7c-4f4e-9f0a-6ca9f52b95da')
    def test_barbican_resources_create_update(self):
        # create: secret, a container referencing it, a key order, and a
        # second container referencing the order's generated secret
        stack_identifier = self.stack_create(template=barbican_template)
        secret_ref = self.get_stack_output(stack_identifier, 'secret_ref')
        container_ref = self.get_stack_output(stack_identifier,
                                              'container_ref')
        order_ref = self.get_stack_output(stack_identifier, 'order_ref')
        order_container_ref = self.get_stack_output(
            stack_identifier, 'order_container_ref')
        self.assertIsNotNone(secret_ref)
        self.assertIsNotNone(container_ref)
        self.assertIsNotNone(order_ref)
        self.assertIsNotNone(order_container_ref)
        # the order generates its secret asynchronously
        self.assertIsNotNone(self.get_stack_output(stack_identifier,
                                                   'order_secret_ref'))

        # immutable resources are replaced on update: refs must change.
        # payload drives the secret/container replace; bit_length drives
        # the order replace, which cascades to the order's container
        parameters = {'payload': 's3cr3t-payload-v2-UPDATED',
                      'bit_length': 192}
        self.update_stack(stack_identifier, barbican_template,
                          parameters=parameters)
        self.assertNotEqual(secret_ref,
                            self.get_stack_output(stack_identifier,
                                                  'secret_ref'))
        self.assertNotEqual(container_ref,
                            self.get_stack_output(stack_identifier,
                                                  'container_ref'))
        self.assertNotEqual(order_ref,
                            self.get_stack_output(stack_identifier,
                                                  'order_ref'))
        self.assertNotEqual(order_container_ref,
                            self.get_stack_output(stack_identifier,
                                                  'order_container_ref'))
