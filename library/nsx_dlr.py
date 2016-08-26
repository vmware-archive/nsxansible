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
    :param dlr_name: The name of the edge searched
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
    params_check_ifaces(module)
    ifaces = construct_ifaces_dict(module.params['interfaces'])

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
    initial_intf = []
    for iface_key, iface in ifaces.items():
        connected_to = None
        if 'portgroup_id' in iface:
            connected_to = iface['portgroup_id']
        elif 'logical_switch' in iface:
            lswitch_id = get_logical_switch(client_session, iface['logical_switch'])
            connected_to = lswitch_id
        initial_intf.append({'name': iface_key, 'type': iface['iftype'], 'isConnected': "True",
                             'connectedToId': connected_to,
                             'addressGroups': {'addressGroup': {'primaryAddress': iface['ip'],
                                                                'subnetPrefixLength': iface['prefix_len']}
                                               }
                             })

    dlr_create_dict['edge']['interfaces'] = {'interface': initial_intf}

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


def params_check_routes(module):
    routes = module.params['routes']
    if not isinstance(routes, list):
        module.fail_json(msg='Malformed Routes List: The routes Information is not a list')
    for route in routes:
        if not isinstance(route, dict):
            module.fail_json(msg='Malformed Interface Dictionary: '
                                 'The Interface {} Information is not a dictionary'.format(route))
        network = route.get('network', None)
        next_hop = route.get('next_hop', None)

        if not (network and next_hop):
            module.fail_json(msg='You are missing one of the following parameter '
                                 'in the routes Dict: network or next_hop')


def check_routes(client_session, dlr_id, current_routes, module):
    changed = None
    params_check_routes(module)

    new_routes = []
    for route in current_routes:
        for route_desired in module.params['routes']:
            if route_desired['network'] == route['network'] and route_desired['next_hop'] == route['nextHop']:
                admin_distance = route_desired.get('admin_distance', '1')
                mtu = route_desired.get('mtu', '1500')
                description = route_desired.get('description')

                if admin_distance != route.get('adminDistance'):
                    route['adminDistance'] = admin_distance
                    changed = True
                if mtu != route.get('mtu'):
                    route['mtu'] = mtu
                    changed = True
                if description != route.get('description'):
                    route['description'] = description
                    changed = True
                new_routes.append(route)
                break
        else:
            changed = True

    for route_desired in module.params['routes']:
        for route in current_routes:
            if route_desired['network'] == route['network'] and route_desired['next_hop'] == route['nextHop']:
                break
        else:
            admin_distance = route_desired.get('admin_distance', '1')
            mtu = route_desired.get('mtu', '1500')
            description = route_desired.get('description')
            new_routes.append({'network': route_desired['network'], 'nextHop': route_desired['next_hop'],
                               'adminDistance': admin_distance, 'mtu': mtu, 'description': description})
            changed = True

    if changed:
        rtg_config = client_session.read('routingConfigStatic', uri_parameters={'edgeId': dlr_id})['body']
        rtg_config['staticRouting']['staticRoutes'] = {'route': new_routes}
        client_session.update('routingConfigStatic', uri_parameters={'edgeId': dlr_id}, request_body_dict=rtg_config)

    return changed


def params_check_ifaces(module):
    ifaces = module.params['interfaces']
    if not isinstance(ifaces, list):
        module.fail_json(msg='Malformed Interfaces List: The Interfaces Information is not a list')
    for iface in ifaces:
        if not isinstance(iface, dict):
            module.fail_json(msg='Malformed Interface Dictionary: '
                                 'The Interface Information is not a dictionary: {}'.format(iface))
        ip = iface.get('ip', None)
        pfx_len = iface.get('prefix_len', None)
        if_type = iface.get('iftype', None)
        lswitch = iface.get('logical_switch', None)
        portgroupid = iface.get('portgroup_id', None)
        name = iface.get('name', None)
        if not (ip and pfx_len and if_type and name):
            module.fail_json(msg='You are missing one of the following parameter '
                                 'in the Interface Dict: ip {} or prefix_len {} or '
                                 'iftype {} or name {}'.format(ip, pfx_len, if_type, name))
        if not (lswitch or portgroupid):
            module.fail_json(msg='You are missing either: logical_switch or portgroup_id as '
                                 'parameters on {}'.format(iface['name']))
        if (lswitch and portgroupid):
            module.fail_json(msg='Interface can either have: logical_switch or portgroup_id as parameters, '
                                 'but not both on {}'.format(iface['name']))


def construct_ifaces_dict(iface_list):
    iface_dict = {}
    for iface in iface_list:
        iface_dict[iface['name']] = iface
    return iface_dict


def check_interfaces(client_session, dlr_id, module):
    changed = None
    params_check_ifaces(module)

    intfs_api = client_session.read('interfaces', uri_parameters={'edgeId': dlr_id})['body']

    if intfs_api['interfaces']:
        intfs = client_session.normalize_list_return(intfs_api['interfaces']['interface'])
    else:
        intfs = []

    current_interfaces = intfs

    intfs_namelist = []
    for intf in intfs:
        intfs_namelist.append(intf['name'])

    ifaces = construct_ifaces_dict(module.params['interfaces'])

    for intf in intfs:
        intf_deletion = None
        idx = intf['name']
        ifindex = intf['index']
        if idx in ifaces.keys():
            continue
        if 'connectedToId' in intf:
            intf_deletion = True
        if intf['addressGroups']:
            intf_deletion = True
        if intf['name'] != idx:
            intf_deletion = True

        if intf_deletion:
            client_session.delete('interface', uri_parameters={'edgeId': dlr_id, 'index': ifindex})
            changed = True

    for intf in intfs:
        intf_changed = None
        idx = intf['name']
        ifindex = intf['index']
        if idx not in ifaces.keys():
            continue

        if intf['type'] != ifaces[idx]['iftype']:
            intf['type'] = ifaces[idx]['iftype']
            intf_changed = True

        if 'portgroup_id' in ifaces[idx]:
            if not 'connectedToId' in intf:
                intf['connectedToId'] = ifaces[idx]['portgroup_id']
                intf_changed = True
            else:
                if intf['connectedToId'] != ifaces[idx]['portgroup_id']:
                    intf['connectedToId'] = ifaces[idx]['portgroup_id']
                    intf_changed = True
        elif 'logical_switch' in ifaces[idx]:
            lswitch_id = get_logical_switch(client_session, ifaces[idx]['logical_switch'])
            if not 'connectedToId' in intf:
                intf['connectedToId'] = lswitch_id
                intf_changed = True
            else:
                if intf['connectedToId'] != lswitch_id:
                    intf['connectedToId'] = lswitch_id
                    intf_changed = True

        if not intf['addressGroups']:
            intf['addressGroups'] = {'addressGroup': {'primaryAddress': ifaces[idx]['ip'],
                                     'subnetPrefixLength': ifaces[idx]['prefix_len']}}
            intf_changed = True
        else:
            if intf['addressGroups']['addressGroup']['primaryAddress'] != ifaces[idx]['ip']:
                intf['addressGroups'] = {'addressGroup': {'primaryAddress': ifaces[idx]['ip'],
                                                          'subnetPrefixLength': str(ifaces[idx]['prefix_len'])}}
                intf_changed = True
            elif intf['addressGroups']['addressGroup']['subnetPrefixLength'] != str(ifaces[idx]['prefix_len']):
                intf['addressGroups'] = {'addressGroup': {'primaryAddress': ifaces[idx]['ip'],
                                                          'subnetPrefixLength': str(ifaces[idx]['prefix_len'])}}
                intf_changed = True

        if intf_changed:
            intf['isConnected'] = 'true'
            intfs_update =  {'interface': intf}
            client_session.update('interface', uri_parameters={'edgeId': dlr_id, 'index': ifindex},
                                  request_body_dict=intfs_update)
            changed = True

    for iface_key, iface in ifaces.items():
        if iface_key not in intfs_namelist:
            connected_to = None
            if 'portgroup_id' in iface:
                connected_to = iface['portgroup_id']
            elif 'logical_switch' in iface:
                lswitch_id = get_logical_switch(client_session, iface['logical_switch'])
                connected_to = lswitch_id
            add_if = {'name': iface_key, 'type': iface['iftype'], 'isConnected': "True",
                      'connectedToId': connected_to,
                      'addressGroups': {'addressGroup': {'primaryAddress': iface['ip'],
                                                         'subnetPrefixLength': iface['prefix_len']}
                                        }
                      }
            client_session.create('interfaces', uri_parameters={'edgeId': dlr_id},
                                  query_parameters_dict={'action': 'patch'},
                                  request_body_dict={'interfaces': {'interface': add_if }}
                                  )
            changed = True

    if changed:
        intfs_api = client_session.read('interfaces', uri_parameters={'edgeId': dlr_id})['body']

        if intfs_api['interfaces']:
            current_interfaces = client_session.normalize_list_return(intfs_api['interfaces']['interface'])
        else:
            current_interfaces = []


    return changed, current_interfaces


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
            interfaces=dict(required=True, type='list'),
            routes=dict(default=[], type='list'),
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

    ifaces_changed, current_interfaces = check_interfaces(client_session, dlr_id, module)
    routes_changed = check_routes(client_session, dlr_id, routes, module)

    if ifaces_changed:
        changed = True
    if routes_changed:
        changed = True

    if module.params['default_gateway']:
        if current_dfgw != module.params['default_gateway']:
            changed = config_def_gw(client_session, dlr_id, module.params['default_gateway'])
    else:
        if current_dfgw:
            changed = config_def_gw(client_session, dlr_id, None)

    if changed:
        module.exit_json(changed=True, interfaces=current_interfaces)
    else:
        module.exit_json(changed=False, interfaces=current_interfaces)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
