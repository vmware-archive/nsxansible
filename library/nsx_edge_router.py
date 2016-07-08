#!/usr/bin/env python
# coding=utf-8
#
# Copyright � 2015 VMware, Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


def get_logical_switch(client_session, logical_switch_name):
    """
    :param client_session: An instance of an NsxClient Session
    :param logical_switch_name: The name of the logical switch searched
    :return: A tuple, with the first item being the logical switch id as string of the first Scope found with the
             right name and the second item being a dictionary of the logical parameters as return by the NSX API
    """
    all_lswitches = client_session.read_all_pages('logicalSwitchesGlobal', 'read')
    try:
        logical_switch_params = [scope for scope in all_lswitches if scope['name'] == logical_switch_name][0]
        logical_switch_id = logical_switch_params['objectId']
    except IndexError:
        return None

    return logical_switch_id


def get_edge(client_session, edge_name):
    """
    :param client_session: An instance of an NsxClient Session
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


def create_edge_service_gateway(session, module):
    create_edge_body = session.extract_resource_body_example('nsxEdges', 'create')

    create_edge_body['edge']['name'] = module.params['name']
    create_edge_body['edge']['description'] = module.params['description']
    create_edge_body['edge']['type'] = 'gatewayServices'
    create_edge_body['edge']['datacenterMoid'] = module.params['datacenter_moid']
    create_edge_body['edge']['appliances']['appliance']['resourcePoolId'] = module.params['resourcepool_moid']
    create_edge_body['edge']['appliances']['appliance']['datastoreId'] = module.params['datastore_moid']
    create_edge_body['edge']['appliances']['appliance']['customField']['key'] = 'system.service.vmware.vsla.main01'
    create_edge_body['edge']['appliances']['appliance']['customField']['value'] = 'string'

    internal_switch_id = get_logical_switch(session,  module.params['edge_int_logicalswitch_name'])

    vnics_info = [{'name': module.params['edge_int_vnic_name'],
                            'index': module.params['edge_int_vnic_index'],
                            'isConnected': 'true',
                            'type': 'internal',
                            'portgroupId': internal_switch_id,
                            'fenceParameter':{'key': 'ethernet0.filter1.param1','value': 1},
                            'addressGroups': {'addressGroup': {'primaryAddress': module.params['edge_int_vnic_ip'],
                                                               'subnetPrefixLength':
                                                                   module.params['edge_int_vnic_subnet_prefix']}}},
                  {'name': module.params['edge_uplink_vnic_name'],
                            'index': module.params['edge_uplink_vnic_index'],
                            'isConnected': 'true',
                            'type': 'uplink',
                            'portgroupId': module.params['edge_uplink_portgroup_moid'],
                            'fenceParameter':{'key': 'ethernet0.filter1.param1','value': 1},
                            'addressGroups': {'addressGroup': 
                                    {'primaryAddress': module.params['edge_uplink_vnic_ip'],
                                     'subnetPrefixLength': module.params['edge_uplink_vnic_subnet_prefix']}},
                                     },]

    create_edge_body['edge']['vnics']['vnic'] = vnics_info

    return session.create('nsxEdges', request_body_dict=create_edge_body)

def delete_edge_service_gateway(client_session, esg_id, module):
    response = client_session.delete('nsxEdge', uri_parameters={'edgeId': esg_id})
    return response


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            name=dict(required=True),
            description=dict(),
            resourcepool_moid=dict(required=True),
            datastore_moid=dict(required=True),
            datacenter_moid=dict(required=True),
            edge_int_vnic_index=dict(required=True),
            edge_int_vnic_name=dict(required=True),
            edge_int_logicalswitch_name=dict(required=True),
            edge_int_vnic_ip=dict(required=True),
            edge_int_vnic_subnet_prefix=dict(required=True),
            edge_uplink_vnic_index=dict(required=True),
            edge_uplink_vnic_name=dict(required=True),
            edge_uplink_portgroup_moid=dict(required=True),
            edge_uplink_vnic_ip=dict(required=True),
            edge_uplink_vnic_subnet_prefix=dict(required=True),
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                               module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'],
                               module.params['nsxmanager_spec']['password'])

    changed = False
    esg_create_response = {}
    esg_delete_response = {}

    if module.params['state'] == 'present':
        edge_id, edge_params = get_edge(client_session, module.params['name'])
        if not edge_id:
            esg_create_response = create_edge_service_gateway(client_session, module)
            changed = True
    elif module.params['state'] == 'absent':
        edge_id, edge_params = get_edge(client_session, module.params['name'])
        if edge_id:
            esg_delete_response = delete_edge_service_gateway(client_session, edge_id, module)
            changed = True

    if changed:
        module.exit_json(changed=True, esg_create_response=esg_create_response,
                         esg_delete_response=esg_delete_response)
    else:
        module.exit_json(changed=False, esg_create_response=esg_create_response,
                         esg_delete_response=esg_delete_response)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
