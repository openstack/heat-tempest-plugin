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

import json
import os
import requests
import subprocess
import sys
import tempfile
import time
import yaml

from oslo_utils import timeutils
from tempest.lib import decorators

from heat_tempest_plugin.common import exceptions
from heat_tempest_plugin.common import test
from heat_tempest_plugin.tests.functional import functional_base


class ParallelDeploymentsTest(functional_base.FunctionalTestsBase):
    server_template = '''
heat_template_version: "2013-05-23"
parameters:
  flavor:
    type: string
  image:
    type: string
  network:
    type: string
resources:
  server:
    type: OS::Nova::Server
    properties:
      image: {get_param: image}
      flavor: {get_param: flavor}
      user_data_format: SOFTWARE_CONFIG
      networks: [{network: {get_param: network}}]
outputs:
  server:
    value: {get_resource: server}
'''

    config_template = '''
heat_template_version: "2013-05-23"
parameters:
  server:
    type: string
resources:
  config:
    type: OS::Heat::SoftwareConfig
    properties:
'''

    deployment_snippet = '''
type: OS::Heat::SoftwareDeployments
properties:
  config: {get_resource: config}
  servers: {'0': {get_param: server}}
'''

    enable_cleanup = True

    @decorators.idempotent_id('8ee231ff-f80a-4a17-a860-5cda87e18ad0')
    def test_deployments_metadata(self):
        parms = {'flavor': self.conf.minimal_instance_type,
                 'network': self.conf.fixed_network_name,
                 'image': self.conf.minimal_image_ref}
        stack_identifier = self.stack_create(
            parameters=parms,
            template=self.server_template,
            enable_cleanup=self.enable_cleanup)
        server_stack = self.client.stacks.get(stack_identifier)
        server = server_stack.outputs[0]['output_value']

        config_stacks = []
        # add up to 3 stacks each with up to 3 deployments
        deploy_count = 0
        deploy_count = self.deploy_many_configs(
            stack_identifier,
            server,
            config_stacks,
            2,
            5,
            deploy_count)
        self.deploy_many_configs(
            stack_identifier,
            server,
            config_stacks,
            3,
            3,
            deploy_count)

        self.signal_deployments(stack_identifier)
        for config_stack in config_stacks:
            self._wait_for_stack_status(config_stack, 'CREATE_COMPLETE')

    @decorators.idempotent_id('bd539232-b999-4bec-b47d-ff4822fc8b82')
    def test_deployments_timeout_failed(self):
        parms = {'flavor': self.conf.minimal_instance_type,
                 'network': self.conf.fixed_network_name,
                 'image': self.conf.minimal_image_ref}
        stack_identifier = self.stack_create(
            parameters=parms,
            template=self.server_template,
            enable_cleanup=self.enable_cleanup)
        server_stack = self.client.stacks.get(stack_identifier)
        server = server_stack.outputs[0]['output_value']
        config_stack = self.deploy_config(server, 3, 1)
        self._wait_for_stack_status(config_stack, 'CREATE_FAILED')
        kwargs = {'server_id': server}

        def check_deployment_status():
            sd_list = self.client.software_deployments.list(**kwargs)
            for sd in sd_list:
                if sd.status != 'FAILED':
                    return False
            return True

        self.assertTrue(test.call_until_true(
            20, 0, check_deployment_status))

    def deploy_many_configs(self, stack, server, config_stacks,
                            stack_count, deploys_per_stack,
                            deploy_count_start):
        for a in range(stack_count):
            config_stacks.append(
                self.deploy_config(server, deploys_per_stack))

        new_count = deploy_count_start + stack_count * deploys_per_stack
        self.wait_for_deploy_metadata_set(stack, new_count)
        return new_count

    def deploy_config(self, server, deploy_count, timeout=None):
        parms = {'server': server}
        template = yaml.safe_load(self.config_template)
        resources = template['resources']
        resources['config']['properties'] = {'config': 'x' * 10000}
        for a in range(deploy_count):
            resources['dep_%s' % a] = yaml.safe_load(self.deployment_snippet)
        return self.stack_create(
            parameters=parms,
            template=template,
            enable_cleanup=self.enable_cleanup,
            expected_status=None,
            timeout=timeout)

    def wait_for_deploy_metadata_set(self, stack, deploy_count):
        build_timeout = self.conf.build_timeout
        build_interval = self.conf.build_interval

        start = timeutils.utcnow()
        while timeutils.delta_seconds(start,
                                      timeutils.utcnow()) < build_timeout:
            server_metadata = self.client.resources.metadata(
                stack, 'server')
            if len(server_metadata['deployments']) == deploy_count:
                return
            time.sleep(build_interval)

        message = ('Deployment resources failed to be created within '
                   'the required time (%s s).' %
                   (build_timeout))
        raise exceptions.TimeoutException(message)

    def signal_deployments(self, stack_identifier):
        server_metadata = self.client.resources.metadata(
            stack_identifier, 'server')
        for dep in server_metadata['deployments']:
            iv = dict((i['name'], i['value']) for i in dep['inputs'])
            sigurl = iv.get('deploy_signal_id')
            requests.post(sigurl, data='{}',
                          headers={'content-type': 'application/json'},
                          verify=self.verify_cert)


@test.requires_service_type('messaging')
@test.requires_service('zaqar')
class ZaqarSignalTransportTest(functional_base.FunctionalTestsBase):
    server_template = '''
heat_template_version: "2013-05-23"

parameters:
  flavor:
    type: string
  image:
    type: string
  network:
    type: string

resources:
  server:
    type: OS::Nova::Server
    properties:
      image: {get_param: image}
      flavor: {get_param: flavor}
      user_data_format: SOFTWARE_CONFIG
      software_config_transport: ZAQAR_MESSAGE
      networks: [{network: {get_param: network}}]
  config:
    type: OS::Heat::SoftwareConfig
    properties:
      config: echo 'foo'
  deployment:
    type: OS::Heat::SoftwareDeployment
    properties:
      config: {get_resource: config}
      server: {get_resource: server}
      signal_transport: ZAQAR_SIGNAL

outputs:
  data:
    value: {get_attr: [deployment, deploy_stdout]}
'''

    conf_template = '''
[zaqar]
user_id = %(user_id)s
password = %(password)s
project_id = %(project_id)s
auth_url = %(auth_url)s
queue_id = %(queue_id)s
    '''

    @decorators.idempotent_id('3af97ced-bead-4629-b78a-97762719e990')
    def test_signal_queues(self):
        parms = {'flavor': self.conf.minimal_instance_type,
                 'network': self.conf.fixed_network_name,
                 'image': self.conf.minimal_image_ref}
        stack_identifier = self.stack_create(
            parameters=parms,
            template=self.server_template,
            expected_status=None)
        metadata = self.wait_for_deploy_metadata_set(stack_identifier)
        config = metadata['os-collect-config']['zaqar']
        conf_content = self.conf_template % config
        fd, temp_path = tempfile.mkstemp()
        os.write(fd, conf_content.encode('utf-8'))
        os.close(fd)
        cmd = ['os-collect-config', '--one-time',
               '--config-file=%s' % temp_path, 'zaqar']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout_value = proc.communicate()[0]
        data = json.loads(stdout_value.decode('utf-8'))
        self.assertEqual(config, data['zaqar']['os-collect-config']['zaqar'])
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout_value = proc.communicate()[0]
        data = json.loads(stdout_value.decode('utf-8'))

        fd, temp_path = tempfile.mkstemp()
        os.write(fd,
                 json.dumps(data['zaqar']['deployments'][0]).encode('utf-8'))
        os.close(fd)
        cmd = [sys.executable, self.conf.heat_config_notify_script, temp_path]
        proc = subprocess.Popen(cmd,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)
        proc.communicate(
            json.dumps({'deploy_stdout': 'here!'}).encode('utf-8'))
        self._wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')
        stack = self.client.stacks.get(stack_identifier)
        self.assertEqual('here!', stack.outputs[0]['output_value'])

    def wait_for_deploy_metadata_set(self, stack):
        build_timeout = self.conf.build_timeout
        build_interval = self.conf.build_interval

        start = timeutils.utcnow()
        while timeutils.delta_seconds(start,
                                      timeutils.utcnow()) < build_timeout:
            server_metadata = self.client.resources.metadata(
                stack, 'server')
            if server_metadata.get('deployments'):
                return server_metadata
            time.sleep(build_interval)

        message = ('Deployment resources failed to be created within '
                   'the required time (%s s).' %
                   (build_timeout))
        raise exceptions.TimeoutException(message)
