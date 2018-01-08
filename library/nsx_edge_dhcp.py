#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2015-2016 VMware, Inc. All Rights Reserved.
#
# Licensed under the X11 (MIT) (the “License”) set forth below;
#
# you may not use this file except in compliance with the License. Unless required by applicable law or agreed to in
# writing, software distributed under the License is distributed on an “AS IS” BASIS, without warranties or conditions
# of any kind, EITHER EXPRESS OR IMPLIED. See the License for the specific language governing permissions and
# limitations under the License. Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# "THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.”

# Portions of this code have been copied from the https://github.com/vmware/pynsxv library
#
# pynsxv/library/nsx_dhcp.py
# Adapted for use with Ansible

__author__ = 'virtualelephant'

def get_edge(client_session, edge_name):
    """
    :param client session: An instance of an NsxClient Session
    :param edge_name: The name of the edge searched
    :return: A tuple, with the first item being the edge or dlr id as string of the first Scope found with the
             right name and the second item being a dictionary of the logical parameters as return by the NSX API
    """
    all_edge = client_session.read_all_pages('nsxEdges', 'read')

    try:
        edge_params = [scope for scope in all_edge if scope['name'] == edge_name][0]
        edge_id = edge_params['objectId']
    except IndexError:
        return None, None

    return edge_id, edge_params


def add_dhcp_pool(client_session, edge_name, ip_range, default_gateway, subnet, domain_name,
                  dns_server_1, dns_server_2, lease_time, auto_dns=None):
    """
    :param client_session: An instance of an NsxClient session
    :param edge_name: The name of the edge searched
    :param ip_range: An IP range for the IP pool
    :param default_gateway: The default gateway for the IP pool
    :param subnet: The subnet of the IP pool
    :param domain_name: The DNS domain name
    :param dns_server_1: The primary DNS for the IP pool
    :param dns_server_2: The secondary DNS for the IP pool
    :param lease_time: The DHCP lease time value, default is 1 day
    :param auto_dns: If set to true, the DNS servers from the NSX Manager will be used
    :return: Returns true or false
    """
    edge_id, edge_params = get_edge(client_session, edge_name)

    if not edge_id:
        return None

    dhcp_pool_dict = {'ipRange': ip_range,
                      'defaultGateway': default_gateway,
                      'subnetMask': subnet,
                      'domainName': domain_name,
                      'primaryNameServer': dns_server_1,
                      'secondaryNameServer': dns_server2,
                      'leaseTime': lease_time,
                      'autoConfigureDNS': auto_dns}

    cfg_result = client_session.create('dhcpPool', uri_parameters={'edgeId': edge_id}, request_body_dict={'ipPool': dhcp_pool_dict})

    if cfg_result['status'] == 204:
        return True
    else:
        return False


def dhcp_server(client_session, edge_name, enabled=None, syslog_enabled=None, syslog_level=None):
    """

    """
    edge_id, edge_params = get_edge(client_session, edge_name)

    if not edge_id:
        return None

    change_needed = False

    # Check current DHCP service status
    current_dhcp_config = client_session.read('dhcp', uri_parameter={'edgeId': edge_id})['body']
    new_dhcp_config = current_dhcp_config

    if enabled:
        if current_dhcp_config['dhcp']['enabled'] == 'false':
            new_dhcp_config['dhcp']['enabled'] = 'true'
            change_needed = True
    else:
        if current_dhcp_config['dhcp']['enabled'] == 'true':
            new_dhcp_config['dhcp']['enabled'] = 'false'
            change_needed = True

    if syslog_level:
        if current_dhcp_config['dhcp']['logging']['logLevel'] != syslog_level:
            new_dhcp_config['dhcp']['logging']['logLevel'] = syslog_level
            change_needed = True

    if not change_needed:
        return True
    else:
        result = client_session.update('dhcp', uri_parameter={'edgeId': edge_id}, request_body_dict=new_dhcp_config)

        if cfg_result['status'] == 204:
            return True
        else:
            return False


def main():
    module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'absent']),
                nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
                name=dict(required=True),
                ip_range=dict(required=True),
                default_gateway=dict(),
                subnet=dict(required=True),
                domain_name=dict(),
                dns_server_1=dict(),
                dns_server_2=dict(),
                lease_time=dict(default='86400'),
                auto_dns=dict(default=False, choices=[True, False])
            ),
            supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                               module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'],
                               module.params['nsxmanager_spec']['password'])

    changed = False
    edge_id, edge_params = get_edge(client_session, module.params['name'])
    
    if changed:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
