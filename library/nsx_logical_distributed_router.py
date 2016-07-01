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

def create_ldr(client_session, module):
    dlr_create_dict = client_session.extract_resource_body_schema('nsxEdges', 'create')

    dlr_create_dict['edge']['name'] = module.params['name']
    dlr_create_dict['edge']['description'] = module.params['description']
    dlr_create_dict['edge']['type'] = 'distributedRouter'
    dlr_create_dict['edge']['datacenterMoid'] = module.params['datacenter_moid']
    dlr_create_dict['edge']['appliances']['appliance']['resourcePoolId'] = module.params['resourcepool_moid']
    dlr_create_dict['edge']['appliances']['appliance']['datastoreId'] = module.params['datastore_moid']
    dlr_create_dict['edge']['mgmtInterface'] = {'connectedToId': module.params['portgroup_moid']}

    # Get logical Switch ID for interface connection
    internal_switch_id = get_logical_switch(client_session,
                            module.params['interface_int_switch_name'])
    uplink_switch_id= get_logical_switch(client_session,
                            module.params['interface_uplink_switch_name'])

    interfaces=[{'name': module.params['uplink_interface_name'],
                             'type': 'uplink',
                             'isConnected': "True",
                             'connectedToId': uplink_switch_id, # second switch connected to uplink
                             'addressGroups': {'addressGroup': 
                                              {'primaryAddress': module.params['interface_uplink_switch_ip'],
                                                'subnetMask': module.params['interface_uplink_switch_subnet_mask']
                                               }}},
               {'name': module.params['internal_interface_name'],
                 'type': 'internal',
                 'isConnected': "True",
                 'connectedToId': internal_switch_id, # first switch connected to internal
                 'addressGroups': {'addressGroup': 
                                  {'primaryAddress': module.params['interface_int_switch_ip'],
                                    'subnetMask': module.params['interface_int_switch_subnet_mask']
                                   }}
                }]
    dlr_create_dict['edge']['interfaces']['interface'] = interfaces
    del dlr_create_dict['edge']['vnics']
    del dlr_create_dict['edge']['appliances']['appliance']['hostId']
    del dlr_create_dict['edge']['appliances']['appliance']['customField']

    return client_session.create('nsxEdges', request_body_dict=dlr_create_dict)

def configure_ha(session, edge_id):
    edge_ha_body = session.extract_resource_body_schema('highAvailability', 'update')
    edge_ha_body['highAvailability']['declareDeadTime'] = 20
    edge_ha_body['highAvailability']['enabled'] = 'true'

    return session.update('highAvailability', uri_parameters={'edgeId': edge_id},
                          request_body_dict=edge_ha_body)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True),
            name=dict(required=True),
            description=dict(),
            resourcepool_moid=dict(required=True),
            datastore_moid=dict(required=True),
            portgroup_moid=dict(required=True),
            datacenter_moid=dict(required=True),
            internal_interface_name=dict(required=True),
            interface_int_switch_name=dict(required=True),
            interface_int_switch_ip=dict(required=True),
            interface_int_switch_subnet_mask=dict(required=True),
            uplink_interface_name=dict(required=True),
            interface_uplink_switch_name=dict(required=True),
            interface_uplink_switch_ip=dict(required=True),
            interface_uplink_switch_subnet_mask=dict(required=True),
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'],
                             module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'],
                             module.params['nsxmanager_spec']['password'])

    ldr_response=create_ldr(client_session, module)

    # Configure HA for deployed Logical Distributed Router
    ha_response = configure_ha(client_session, ldr_response['objectId'])

    module.exit_json(changed=True, argument_spec=module.params['state'],
                     ldr_response=ldr_response)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
