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


server_with_sub_fixed_ip_template = '''
heat_template_version: 2016-04-08
description: Test template to test nova server with subnet and fixed_ip.
parameters:
  flavor:
    type: string
  image:
    type: string
resources:
  net:
    type: OS::Neutron::Net
    properties:
      name: my_net
  subnet:
    type: OS::Neutron::Subnet
    properties:
      network: {get_resource: net}
      cidr: 11.11.11.0/24
  security_group:
    type: OS::Neutron::SecurityGroup
    properties:
      name: the_sg
      description: Ping and SSH
      rules:
      - protocol: icmp
      - protocol: tcp
        port_range_min: 22
        port_range_max: 22
  server:
    type: OS::Nova::Server
    properties:
      image: {get_param: image}
      flavor: {get_param: flavor}
      networks:
        - subnet: {get_resource: subnet}
          fixed_ip: 11.11.11.11
      security_groups:
        - {get_resource: security_group}
outputs:
  networks:
    value: {get_attr: [server, networks]}
'''

server_with_port_template = '''
heat_template_version: 2016-04-08
description: Test template to test nova server with port.
parameters:
  flavor:
    type: string
  image:
    type: string
resources:
  net:
    type: OS::Neutron::Net
    properties:
      name: server_with_port_net
  subnet:
    type: OS::Neutron::Subnet
    properties:
      network: {get_resource: net}
      cidr: 11.11.11.0/24
  port:
    type: OS::Neutron::Port
    properties:
      network: {get_resource: net}
      fixed_ips:
        - subnet: {get_resource: subnet}
          ip_address: 11.11.11.11
  server:
    type: OS::Nova::Server
    properties:
      image: {get_param: image}
      flavor: {get_param: flavor}
      networks:
        - port: {get_resource: port}
'''

server_with_multiple_subnets_no_ports_template = '''
heat_template_version: 2016-04-08
description: Test template to test nova server network updates.
parameters:
  flavor:
    type: string
  image:
    type: string
resources:
  net:
    type: OS::Neutron::Net
    properties:
      name: the_net
  subnet_a:
    type: OS::Neutron::Subnet
    properties:
      network: {get_resource: net}
      cidr: 11.11.11.0/24
      name: subnet_a
  subnet_b:
    type: OS::Neutron::Subnet
    properties:
      network: {get_resource: net}
      cidr: 12.12.12.0/24
      name: subnet_b
  server:
    type: OS::Nova::Server
    properties:
      image: {get_param: image}
      flavor: {get_param: flavor}
      networks: $NETWORKS
outputs:
  networks:
    value: {get_attr: [server, networks]}
'''

server_with_no_nets_template = '''
heat_template_version: 2016-04-08
description: Test template to test nova server network updates.
parameters:
  flavor:
    type: string
  image:
    type: string
resources:
  net:
    type: OS::Neutron::Net
    properties:
      name: the_net
  subnet:
    type: OS::Neutron::Subnet
    properties:
      name: the_subnet
      network: {get_resource: net}
      cidr: 11.11.11.0/24
  server:
    type: OS::Nova::Server
    properties:
      image: {get_param: image}
      flavor: {get_param: flavor}
      networks: $NETWORKS
outputs:
  port0_id:
    value: {get_attr: [server, addresses, the_net, 0, port]}
  port1_id:
    value: {get_attr: [server, addresses, the_net, 1, port]}
  port2_id:
    value: {get_attr: [server, addresses, the_net, 2, port]}
  port0_ip_addr:
    value: {get_attr: [server, addresses, the_net, 0, addr]}
  port1_ip_addr:
    value: {get_attr: [server, addresses, the_net, 1, addr]}
  port2_ip_addr:
    value: {get_attr: [server, addresses, the_net, 2, addr]}
'''


class CreateServerTest(functional_base.FunctionalTestsBase):

    def get_outputs(self, stack_identifier, output_key):
        stack = self.client.stacks.get(stack_identifier)
        return self._stack_output(stack, output_key)

    @decorators.idempotent_id('58ccf0aa-7531-4eaa-8ed5-38663a4defaa')
    def test_create_server_with_subnet_fixed_ip_sec_group(self):
        parms = {'flavor': self.conf.minimal_instance_type,
                 'image': self.conf.minimal_image_ref}
        stack_identifier = self.stack_create(
            template=server_with_sub_fixed_ip_template,
            stack_name='server_with_sub_ip',
            parameters=parms)

        networks = self.get_outputs(stack_identifier, 'networks')
        self.assertEqual(['11.11.11.11'], networks['my_net'])

        server_resource = self.client.resources.get(
            stack_identifier, 'server')
        server_id = server_resource.physical_resource_id
        server = self.compute_client.servers.get(server_id)
        self.assertEqual([{"name": "the_sg"}], server.security_groups)

    @decorators.idempotent_id('12185eaa-927f-43f3-a525-0424c4eb9b5d')
    def test_create_update_server_with_subnet(self):
        parms = {'flavor': self.conf.minimal_instance_type,
                 'image': self.conf.minimal_image_ref}
        template = server_with_multiple_subnets_no_ports_template.replace(
            '$NETWORKS', ('[{subnet: {get_resource: subnet_a}}]'))
        stack_identifier = self.stack_create(
            template=template,
            stack_name='create_server_with_sub_ip',
            parameters=parms)
        networks = self.get_outputs(stack_identifier, 'networks')
        self.assertIn('11.11.11', networks['the_net'][0])

        # update the server using a different subnet, we won't pass
        # both port_id and net_id to attach interface, then update success
        template = server_with_multiple_subnets_no_ports_template.replace(
            '$NETWORKS', ('[{subnet: {get_resource: subnet_b}}]'))
        self.update_stack(stack_identifier,
                          template,
                          parameters=parms)
        new_networks = self.get_outputs(stack_identifier, 'networks')
        self.assertNotIn('11.11.11', new_networks['the_net'][0])
        self.assertIn('12.12.12', new_networks['the_net'][0])

    @decorators.idempotent_id('19479c15-6b25-4865-8889-658566608bd9')
    def test_create_server_with_port(self):
        parms = {'flavor': self.conf.minimal_instance_type,
                 'image': self.conf.minimal_image_ref}
        # We just want to make sure we can create the server, no need to assert
        # anything
        self.stack_create(
            template=server_with_port_template,
            stack_name='server_with_port',
            parameters=parms)


class UpdateServerNetworksTest(functional_base.FunctionalTestsBase):
    def setUp(self):
        super(UpdateServerNetworksTest, self).setUp()
        self.params = {'flavor': self.conf.minimal_instance_type,
                       'image': self.conf.minimal_image_ref}

    def get_outputs(self, stack_identifier, output_key):
        stack = self.client.stacks.get(stack_identifier)
        return self._stack_output(stack, output_key)

    @decorators.idempotent_id('c1a22dbf-3160-41b7-8d3f-62ca33fc35a8')
    def test_create_update_server_swap_network_subnet(self):
        '''Test updating stack with:

        old_snippet
          networks:
            - network: {get_resource: net}
        new_snippet
          networks:
            - subnet: {get_resource: subnet}
        '''
        template = server_with_no_nets_template.replace(
            '$NETWORKS', '[{network: {get_resource: net}}]')
        stack_identifier = self.stack_create(
            template=template,
            stack_name='swap_network_subnet',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS', '[{subnet: {get_resource: subnet}}]')
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))

    @decorators.idempotent_id('cccfe612-1ab7-401f-a4c5-63372826a780')
    def test_create_update_server_swap_network_port(self):
        '''Test updating stack with:

        old_snippet
          networks:
            - network: {get_resource: net}
        new_snippet
          networks:
            - port: <the_port_created_on_stack_create>
        '''
        template = server_with_no_nets_template.replace(
            '$NETWORKS', '[{network: {get_resource: net}}]')
        stack_identifier = self.stack_create(
            template=template,
            stack_name='swap_network_port',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS', '[{port: ' + port0 + '}]')
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))

    @decorators.idempotent_id('3eeb0dff-5d2d-4178-a4e6-06e4c26ce23a')
    def test_create_update_server_swap_subnet_network(self):
        '''Test updating stack with:

        old_snippet
          networks:
            - subnet: {get_resource: subnet}
        new_snippet
          networks:
            - network: {get_resource: net}
        '''
        template = server_with_no_nets_template.replace(
            '$NETWORKS', '[{subnet: {get_resource: subnet}}]')
        stack_identifier = self.stack_create(
            template=template,
            stack_name='swap_subnet_network',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS', '[{network: {get_resource: net}}]')
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))

    @decorators.idempotent_id('647fda5d-fc0c-4eb1-9ce3-c4c537461324')
    def test_create_update_server_add_subnet(self):
        '''Test updating stack with:

        old_snippet
          networks:
            - network: {get_resource: net}
        new_snippet
          networks:
            - network: {get_resource: net}
              subnet: {get_resource: subnet}
        '''
        template = server_with_no_nets_template.replace(
            '$NETWORKS', '[{network: {get_resource: net}}]')
        stack_identifier = self.stack_create(
            template=template,
            stack_name='add_subnet',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS',
            '[{network: {get_resource: net}, subnet: {get_resource: subnet}}]')
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))

    @decorators.idempotent_id('01c0f1cd-25b2-49b9-b4ac-fc4dd8937e42')
    def test_create_update_server_add_same_fixed_ip(self):
        '''Test updating stack with:

        old_snippet
          networks:
            - network: {get_resource: net}
        new_snippet
          networks:
            - network: {get_resource: net}
              fixed_ip: <the_same_ip_already_allocated>
        '''
        template = server_with_no_nets_template.replace(
            '$NETWORKS',
            '[{network: {get_resource: net}}]')
        stack_identifier = self.stack_create(
            template=template,
            stack_name='same_fixed_ip',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        port0_ip = self.get_outputs(stack_identifier, 'port0_ip_addr')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS',
            '[{network: {get_resource: net}, fixed_ip: ' + port0_ip + '}]')
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))

    @decorators.idempotent_id('abc39cd6-7745-4314-ac04-85df532dd7c9')
    def test_create_update_server_add_network(self):
        '''Test updating stack with:

        old_snippet
          networks:
            - subnet: {get_resource: subnet}
        new_snippet
          networks:
            - network: {get_resource: net}
              subnet: {get_resource: subnet}
        '''
        template = server_with_no_nets_template.replace(
            '$NETWORKS', '[{subnet: {get_resource: subnet}}]')
        stack_identifier = self.stack_create(
            template=template,
            stack_name='add_network',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS',
            '[{network: {get_resource: net}, subnet: {get_resource: subnet}}]')
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))

    @decorators.idempotent_id('3f729e7e-a698-4ee3-8a5e-0db84f16d1e1')
    def test_create_update_server_multi_networks_swaps(self):
        '''Test updating stack with:

         old_snippet:
           networks:
             - network: {get_resource: net}
             - network: {get_resource: net}
               fixed_ip: 11.11.11.33
             - subnet: {get_resource: subnet}
         new_snippet:
           networks:
             - subnet: {get_resource: subnet}
             - network: {get_resource: net}
             - network: {get_resource: net}
               subnet: {get_resource: subnet}
        '''
        old_snippet = """
        - network: {get_resource: net}
        - network: {get_resource: net}
          fixed_ip: 11.11.11.33
        - subnet: {get_resource: subnet}
"""
        new_snippet = """
        - subnet: {get_resource: subnet}
        - network: {get_resource: net}
        - network: {get_resource: net}
          subnet: {get_resource: subnet}
"""
        template = server_with_no_nets_template.replace(
            '$NETWORKS', old_snippet)
        stack_identifier = self.stack_create(
            template=template,
            stack_name='multi_networks_swaps',
            parameters=self.params)
        port0 = self.get_outputs(stack_identifier, 'port0_id')
        port1 = self.get_outputs(stack_identifier, 'port1_id')
        port2 = self.get_outputs(stack_identifier, 'port2_id')
        template_update = server_with_no_nets_template.replace(
            '$NETWORKS', new_snippet)
        self.update_stack(stack_identifier, template_update,
                          parameters=self.params)
        self.assertEqual(port0, self.get_outputs(stack_identifier, 'port0_id'))
        self.assertEqual(port1, self.get_outputs(stack_identifier, 'port1_id'))
        self.assertEqual(port2, self.get_outputs(stack_identifier, 'port2_id'))
