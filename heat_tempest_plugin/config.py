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

from oslo_config import cfg

import os

default_template = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'tests/scenario/templates/boot_config_none_env.yaml')

service_available_group = cfg.OptGroup(name="service_available",
                                       title="Available OpenStack Services")

ServiceAvailableGroup = [
    cfg.BoolOpt("heat",
                default=True,
                help="Whether or not heat is expected to be available",
                deprecated_opts=[cfg.DeprecatedOpt(
                    'heat_plugin',
                    group='service_available')]),
]

heat_group = cfg.OptGroup(name="heat_plugin",
                          title="Heat Service Options")

HeatGroup = [
    cfg.StrOpt("catalog_type",
               default="orchestration",
               help="Catalog type of the orchestration service."),
    cfg.StrOpt('username',
               help="Username to use for non admin API requests."),
    cfg.StrOpt('password',
               help="Non admin API key to use when authenticating.",
               secret=True),
    cfg.StrOpt('admin_username',
               help="Username to use for admin API requests."),
    cfg.StrOpt('admin_password',
               help="Admin API key to use when authentication.",
               secret=True),
    cfg.StrOpt('project_name',
               help="Project name to use for API requests.",
               deprecated_opts=[cfg.DeprecatedOpt(
                   'tenant_name', group='heat_plugin')]),
    cfg.StrOpt('admin_project_name',
               default='admin',
               help="Admin project name to use for admin API requests.",
               deprecated_opts=[cfg.DeprecatedOpt(
                   'admin_tenant_name', group='heat_plugin')]),
    cfg.StrOpt('auth_url',
               help="Full URI of the OpenStack Identity API (Keystone)."),
    cfg.StrOpt('auth_version',
               deprecated_for_removal=True,
               deprecated_reason='Identity v2 API was removed and v3 is '
                                 'the only available identity API version now',
               help="OpenStack Identity API version."),
    cfg.StrOpt('user_domain_name',
               help="User domain name, if keystone v3 auth_url "
                    "is used"),
    cfg.StrOpt('project_domain_name',
               help="Project domain name, if keystone v3 auth_url "
                    "is used"),
    cfg.StrOpt('user_domain_id',
               help="User domain id, if keystone v3 auth_url "
                    "is used"),
    cfg.StrOpt('project_domain_id',
               help="Project domain id, if keystone v3 auth_url "
                    "is used"),
    cfg.StrOpt('region',
               help="The region name to use"),
    cfg.StrOpt('endpoint_type',
               default='public',
               choices=['public', 'admin', 'internal'],
               help="The endpoint type to use for the orchestration service."),
    cfg.StrOpt('instance_type',
               help="Instance type for tests. Needs to be big enough for a "
                    "full OS plus the test workload"),
    cfg.StrOpt('minimal_instance_type',
               help="Instance type enough for simplest cases."),
    cfg.StrOpt('image_ref',
               help="Name of image to use for tests which boot servers."),
    cfg.StrOpt('keypair_name',
               help="Name of existing keypair to launch servers with."),
    cfg.StrOpt('minimal_image_ref',
               help="Name of minimal (e.g cirros) image to use when "
                    "launching test instances."),
    cfg.BoolOpt('disable_ssl_certificate_validation',
                default=False,
                help="Set to True if using self-signed SSL certificates."),
    cfg.StrOpt('ca_file',
               help="CA certificate to pass for servers that have "
                    "https endpoint."),
    cfg.IntOpt('build_interval',
               default=4,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=1200,
               help="Timeout in seconds to wait for a stack to build."),
    cfg.StrOpt('network_for_ssh',
               default='heat-net',
               help="Network used for SSH connections."),
    cfg.StrOpt('fixed_network_name',
               default='heat-net',
               help="Visible fixed network name "),
    cfg.StrOpt('floating_network_name',
               default='public',
               help="Visible floating network name "),
    cfg.StrOpt('boot_config_env',
               default=default_template,
               help="Path to environment file which defines the "
                    "resource type Heat::InstallConfigAgent. Needs to "
                    "be appropriate for the image_ref."),
    cfg.StrOpt('fixed_subnet_name',
               default='heat-subnet',
               help="Visible fixed sub-network name "),
    cfg.IntOpt('ssh_timeout',
               default=300,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
    cfg.IntOpt('ip_version_for_ssh',
               default=4,
               help="IP version used for SSH connections."),
    cfg.IntOpt('ssh_channel_timeout',
               default=60,
               help="Timeout in seconds to wait for output from ssh "
                    "channel."),
    cfg.BoolOpt('skip_scenario_tests',
                default=False,
                help="Skip all scenario tests"),
    cfg.BoolOpt('skip_functional_tests',
                default=False,
                help="Skip all functional tests"),
    cfg.ListOpt('skip_functional_test_list',
                help="List of functional test class or class.method "
                     "names to skip ex. AutoscalingGroupTest, "
                     "InstanceGroupBasicTest.test_size_updates_work"),
    cfg.ListOpt('skip_scenario_test_list',
                help="List of scenario test class or class.method "
                     "names to skip ex. NeutronLoadBalancerTest, "
                     "AodhAlarmTest.test_alarm"),
    cfg.ListOpt('skip_test_stack_action_list',
                help="List of stack actions in tests to skip "
                     "ex. ABANDON, ADOPT, SUSPEND, RESUME"),
    cfg.BoolOpt('convergence_engine_enabled',
                default=True,
                help="Test features that are only present for stacks with "
                     "convergence enabled."),
    cfg.IntOpt('volume_size',
               default=1,
               help='Default size in GB for volumes created by volumes tests'),
    cfg.IntOpt('connectivity_timeout',
               default=120,
               help="Timeout in seconds to wait for connectivity to "
                    "server."),
    cfg.StrOpt('heat_config_notify_script',
               default=('heat-config-notify'),
               help="Path to the script heat-config-notify"),
    cfg.StrOpt('hidden_stack_tag',
               default='data-processing-cluster',
               help="Tag to be considered as hidden for stack tags tests"),
    cfg.StrOpt('credential_secret_id',
               help="Barbican secret id which storing cloud credential in "
               "remote site."),
    cfg.ListOpt('dns_servers',
                default=(['8.8.8.8', '8.8.4.4']),
                help='Configure custom DNS servers'),
    cfg.BoolOpt('vm_to_heat_api_insecure',
                default=False,
                help="Set this to True if VM images used for tests "
                     "can not verify a (self-signed) SSL certificate "
                     "of public Heat endpoint."),
]

heat_features_group = cfg.OptGroup(
    name='heat_features_enabled',
    title="Enabled Orchestration Service Features")

HeatFeaturesGroup = [
    cfg.BoolOpt('stack_cancel',
                default=False,
                help="If false, skip stack cancel tests"),
    cfg.BoolOpt('multi_cloud',
                default=False,
                help="If false, skip multi-cloud tests for remote stack")
]


def list_opts():
    yield heat_group.name, HeatGroup
    yield heat_features_group.name, HeatFeaturesGroup
    yield service_available_group.name, ServiceAvailableGroup
