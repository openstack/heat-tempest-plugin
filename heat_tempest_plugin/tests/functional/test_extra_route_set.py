# Copyright 2019 Ericsson Software Technology
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

import yaml

from oslo_log import log
from tempest.lib import decorators

from heat_tempest_plugin.common import test
from heat_tempest_plugin.tests.functional import functional_base


LOG = log.getLogger(__name__)

test_template = '''
heat_template_version: pike
description: Test template for OS::Neutron::ExtraRouteSet
resources:
  net0:
    type: OS::Neutron::Net
  subnet0:
    type: OS::Neutron::Subnet
    properties:
      network: { get_resource: net0 }
      cidr: 10.0.0.0/24
  router0:
    type: OS::Neutron::Router
  routerinterface0:
    type: OS::Neutron::RouterInterface
    properties:
      router: { get_resource: router0 }
      subnet: { get_resource: subnet0 }
  extrarouteset0:
    type: OS::Neutron::ExtraRouteSet
    properties:
      router: { get_resource: router0 }
      routes:
        - destination: 10.0.10.0/24
          nexthop: 10.0.0.10
        - destination: 10.0.11.0/24
          nexthop: 10.0.0.11
'''


def _routes_to_set(routes):
    '''Convert a list of extra routes to an unordered data type.'''
    return set(frozenset(r.items()) for r in routes)


@test.requires_resource_type('OS::Neutron::ExtraRouteSet')
class ExtraRouteSetTest(functional_base.FunctionalTestsBase):

    def _create(self, template_routes):
        parsed_template = yaml.safe_load(test_template)
        parsed_template['resources'][
            'extrarouteset0']['properties']['routes'] = template_routes
        create_template = yaml.safe_dump(parsed_template)

        stack_id = self.stack_create(template=create_template)

        neutron_router_id = self.get_physical_resource_id(
            stack_id, 'router0')
        neutron_router = self.network_client.show_router(
            neutron_router_id)['router']
        neutron_routes = neutron_router['routes']

        self.assertEqual(
            _routes_to_set(template_routes),
            _routes_to_set(neutron_routes))

    @decorators.idempotent_id('95b92c1e-d082-11e9-9e5d-9bdb7311b69b')
    def test_create_no(self):
        self._create(template_routes=[])

    @decorators.idempotent_id('abda6884-d0b2-11e9-9819-4f4e24c86c92')
    def test_create_one(self):
        self._create(template_routes=[
            {'destination': '10.0.10.0/24', 'nexthop': '10.0.0.10'},
        ])

    @decorators.idempotent_id('b3a9b6be-d0b2-11e9-a504-7b3ba6df5e7a')
    def test_create_many(self):
        self._create(template_routes=[
            {'destination': '10.0.10.0/24', 'nexthop': '10.0.0.10'},
            {'destination': '10.0.11.0/24', 'nexthop': '10.0.0.11'},
        ])

    def _update(self, template_routes):
        stack_id = self.stack_create(template=test_template)

        parsed_template = yaml.safe_load(test_template)
        parsed_template['resources'][
            'extrarouteset0']['properties']['routes'] = template_routes
        updated_template = yaml.safe_dump(parsed_template)
        self.update_stack(stack_id, updated_template)

        neutron_router_id = self.get_physical_resource_id(
            stack_id, 'router0')
        neutron_router = self.network_client.show_router(
            neutron_router_id)['router']
        neutron_routes = neutron_router['routes']

        self.assertEqual(
            _routes_to_set(template_routes),
            _routes_to_set(neutron_routes))

    @decorators.idempotent_id('6dcf2110-d0b7-11e9-b26b-9f2e5e98d09d')
    def test_update_no(self):
        self._update(template_routes=[])

    @decorators.idempotent_id('6e3cea1a-d0b7-11e9-aebc-f7922b833ea5')
    def test_update_one(self):
        self._update(template_routes=[
            {'destination': '10.0.10.0/24', 'nexthop': '10.0.0.10'},
        ])

    @decorators.idempotent_id('6e970126-d0b7-11e9-8ec8-afde1e726d0f')
    def test_update_many(self):
        self._update(template_routes=[
            {'destination': '10.0.10.0/24', 'nexthop': '10.0.0.10'},
            {'destination': '10.0.11.0/24', 'nexthop': '10.0.0.11'},
        ])
