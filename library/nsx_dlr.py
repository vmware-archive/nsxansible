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


def get_dlr(client_session, dlr_name):
    """
    :param client_session: An instance of an NsxClient Session
    :param edge_name: The name of the edge searched
    :return: A tuple, with the first item being the edge or dlr id as string of the first Scope found with the
             right name and the second item being a dictionary of the logical parameters as return by the NSX API
    """
    all_edge = client_session.read_all_pages('nsxEdges', 'read')

    try:
        edge_params = [scope for scope in all_edge if scope['name'] == dlr_name][0]
        edge_id = edge_params['objectId']
    except IndexError:
        return None, None

    return edge_id, edge_params


def delete_dlr(client_session, dlr_id, module):
    response = client_session.delete('nsxEdge', uri_parameters={'edgeId': dlr_id})
    return response


def create_dlr(client_session, module):
    dlr_create_dict = client_session.extract_resource_body_example('nsxEdges', 'create')

    dlr_create_dict['edge']['name'] = module.params['name']
    dlr_create_dict['edge']['description'] = module.params['description']
    dlr_create_dict['edge']['type'] = 'distributedRouter'
    dlr_create_dict['edge']['datacenterMoid'] = module.params['datacenter_moid']
    dlr_create_dict['edge']['appliances']['appliance']['resourcePoolId'] = module.params['resourcepool_moid']
    dlr_create_dict['edge']['appliances']['appliance']['datastoreId'] = module.params['datastore_moid']
    dlr_create_dict['edge']['mgmtInterface'] = {'connectedToId': module.params['mgmt_portgroup_moid']}
    if module.params['username'] and module.params['password']:
        dlr_create_dict['edge']['cliSettings'] = {'password': module.params['password'],
                                                  'remoteAccess': module.params['remote_access'],
                                                  'userName': module.params['username']}

    # Get logical Switch ID for interface connection
    internal_switch_id = get_logical_switch(client_session, module.params['interface_int_logicalswitch_name'])
    uplink_switch_id = get_logical_switch(client_session, module.params['interface_uplink_logicalswitch_name'])

    interfaces=[{'name': module.params['uplink_interface_name'],
                             'type': 'uplink',
                             'isConnected': "True",
                             'connectedToId': uplink_switch_id, # second switch connected to uplink
                             'addressGroups': {'addressGroup': 
                                              {'primaryAddress': module.params['interface_uplink_ip'],
                                                'subnetMask': module.params['interface_uplink_subnet_mask']
                                               }}},
               {'name': module.params['internal_interface_name'],
                 'type': 'internal',
                 'isConnected': "True",
                 'connectedToId': internal_switch_id, # first switch connected to internal
                 'addressGroups': {'addressGroup': 
                                  {'primaryAddress': module.params['interface_int_ip'],
                                    'subnetMask': module.params['interface_int_subnet_mask']
                                   }}
                }]

    dlr_create_dict['edge']['interfaces'] = {'interface': interfaces}

    del dlr_create_dict['edge']['vnics']
    del dlr_create_dict['edge']['appliances']['appliance']['hostId']
    del dlr_create_dict['edge']['appliances']['appliance']['customField']

    response = client_session.create('nsxEdges', request_body_dict=dlr_create_dict)

    edge_id = response['objectId']
    edge_params = response['body']

    return edge_id, edge_params


def check_ha_status(client_session, dlr_id):
    edge_ha_status = client_session.read('highAvailability', uri_parameters={'edgeId': dlr_id})['body']
    if edge_ha_status['highAvailability']['enabled'] == 'false':
        return False
    elif edge_ha_status['highAvailability']['enabled'] == 'true':
        return True


def configure_ha(session, edge_id, state, dead_time):
    edge_ha_body = session.extract_resource_body_example('highAvailability', 'update')
    edge_ha_body['highAvailability']['declareDeadTime'] = dead_time
    edge_ha_body['highAvailability']['enabled'] = state

    return session.update('highAvailability', uri_parameters={'edgeId': edge_id},
                          request_body_dict=edge_ha_body)


def get_dlr_routes(client_session, dlr_id):
    rtg_cfg = client_session.read('routingConfigStatic', uri_parameters={'edgeId': dlr_id})['body']
    if rtg_cfg['staticRouting']['staticRoutes']:
        routes = client_session.normalize_list_return(rtg_cfg['staticRouting']['staticRoutes']['route'])
    else:
        routes = []

    dfgw_dict = rtg_cfg['staticRouting'].get('defaultRoute', '')
    if dfgw_dict != '':
        dfgw = dfgw_dict.get('gatewayAddress', '')
    else:
        dfgw = None

    return routes, dfgw


def config_def_gw(client_session, dlr_id, dfgw):
    rtg_cfg = client_session.read('routingConfigStatic', uri_parameters={'edgeId': dlr_id})['body']
    if dfgw:
        try:
            rtg_cfg['staticRouting']['defaultRoute']['gatewayAddress'] = dfgw
        except KeyError:
            rtg_cfg['staticRouting']['defaultRoute'] = {'gatewayAddress': dfgw, 'adminDistance': '1', 'mtu': '1500'}
    else:
        rtg_cfg['staticRouting']['defaultRoute'] = None

    cfg_result = client_session.update('routingConfigStatic', uri_parameters={'edgeId': dlr_id},
                                       request_body_dict=rtg_cfg)
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
            description=dict(),
            resourcepool_moid=dict(required=True),
            datastore_moid=dict(required=True),
            mgmt_portgroup_moid=dict(required=True),
            datacenter_moid=dict(required=True),
            internal_interface_name=dict(required=True),
            interface_int_logicalswitch_name=dict(required=True),
            interface_int_ip=dict(required=True),
            interface_int_subnet_mask=dict(required=True),
            uplink_interface_name=dict(required=True),
            interface_uplink_logicalswitch_name=dict(required=True),
            interface_uplink_ip=dict(required=True),
            interface_uplink_subnet_mask=dict(required=True),
            default_gateway=dict(),
            username=dict(),
            password=dict(),
            remote_access=dict(default='false', choices=['true', 'false']),
            ha_enabled=dict(default='false', choices=['true', 'false']),
            ha_deadtime=dict(default='15')
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'],
                             module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'],
                             module.params['nsxmanager_spec']['password'])

    if module.params['remote_access'] == 'true' and not (module.params['password'] and module.params['username']):
        module.fail_json(msg='if remote access is enabled, username and password must be set')

    changed = False
    dlr_create_response = {}
    dlr_delete_response = {}
    dlr_id = None

    if module.params['state'] == 'present':
        dlr_id, dlr_params = get_dlr(client_session, module.params['name'])
        if not dlr_id:
            dlr_id, dlr_params = create_dlr(client_session, module)
            changed = True
    elif module.params['state'] == 'absent':
        dlr_id, dlr_params = get_dlr(client_session, module.params['name'])
        if dlr_id:
            dlr_delete_response = delete_dlr(client_session, dlr_id, module)
            module.exit_json(changed=True, dlr_create_response=dlr_create_response,
                             dlr_delete_response=dlr_delete_response)
        else:
            module.exit_json(changed=False, dlr_create_response=dlr_create_response,
                             dlr_delete_response=dlr_delete_response)

    routes, current_dfgw = get_dlr_routes(client_session, dlr_id)
    ha_state = check_ha_status(client_session, dlr_id)

    if not ha_state and module.params['ha_enabled'] == 'true':
        configure_ha(client_session, dlr_id, module.params['ha_enabled'], module.params['ha_deadtime'])
        changed = True
    elif ha_state and module.params['ha_enabled'] == 'false':
        configure_ha(client_session, dlr_id, module.params['ha_enabled'], module.params['ha_deadtime'])
        changed = True

    if module.params['default_gateway']:
        if current_dfgw != module.params['default_gateway']:
            changed = config_def_gw(client_session, dlr_id, module.params['default_gateway'])
    else:
        if current_dfgw:
            changed = config_def_gw(client_session, dlr_id, None)

    if changed:
        module.exit_json(changed=True, dlr_create_response=dlr_create_response,
                         dlr_delete_response=dlr_delete_response)
    else:
        module.exit_json(changed=False, dlr_create_response=dlr_create_response,
                         dlr_delete_response=dlr_delete_response)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
