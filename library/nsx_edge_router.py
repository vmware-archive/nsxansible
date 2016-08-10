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


def create_edge_service_gateway(client_session, module):
    create_edge_body = client_session.extract_resource_body_example('nsxEdges', 'create')

    create_edge_body['edge']['name'] = module.params['name']
    create_edge_body['edge']['description'] = module.params['description']
    create_edge_body['edge']['type'] = 'gatewayServices'
    create_edge_body['edge']['datacenterMoid'] = module.params['datacenter_moid']
    create_edge_body['edge']['appliances']['applianceSize'] = module.params['appliance_size']
    create_edge_body['edge']['appliances']['appliance']['resourcePoolId'] = module.params['resourcepool_moid']
    create_edge_body['edge']['appliances']['appliance']['datastoreId'] = module.params['datastore_moid']
    create_edge_body['edge']['appliances']['appliance']['customField']['key'] = 'system.service.vmware.vsla.main01'
    create_edge_body['edge']['appliances']['appliance']['customField']['value'] = 'string'
    if module.params['username'] and module.params['password']:
        create_edge_body['edge']['cliSettings'] = {'password': module.params['password'],
                                                   'remoteAccess': module.params['remote_access'],
                                                   'userName': module.params['username']}

    create_edge_body['edge']['vnics']['vnic'] = create_init_ifaces(client_session, module)

    response = client_session.create('nsxEdges', request_body_dict=create_edge_body)
    edge_id = response['objectId']
    edge_params = response['body']

    return edge_id, edge_params


def create_init_ifaces(client_session, module):
    ifaces = module.params['interfaces']
    params_check_ifaces(module)
    vnics_info = []

    for iface_key, iface in ifaces.items():
        iface_index = iface_key[-1:]
        portgroup_id = None
        if 'portgroup_id' in iface:
            portgroup_id = iface['portgroup_id']
        elif 'logical_switch' in iface:
            lswitch_id = get_logical_switch(client_session, iface['logical_switch'])
            portgroup_id = lswitch_id

        fence_param = None
        if 'fence_param' in iface:
            fence_key, fence_val = iface['fence_param'].split('=')
            fence_param = {'key': fence_key,'value': fence_val}

        vnics_info.append({'name': iface['name'], 'index': iface_index, 'isConnected': 'true', 'type': iface['iftype'],
                           'portgroupId': portgroup_id, 'fenceParameter': fence_param,
                           'addressGroups': {'addressGroup': {'primaryAddress': iface['ip'],
                                                              'subnetPrefixLength': iface['prefix_len']}
                                             }
                           })

    return vnics_info

def delete_edge_service_gateway(client_session, esg_id):
    response = client_session.delete('nsxEdge', uri_parameters={'edgeId': esg_id})
    return response


def get_esg_routes(client_session, esg_id):
    rtg_cfg = client_session.read('routingConfigStatic', uri_parameters={'edgeId': esg_id})['body']
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


def config_def_gw(client_session, esg_id, dfgw):
    rtg_cfg = client_session.read('routingConfigStatic', uri_parameters={'edgeId': esg_id})['body']
    if dfgw:
        try:
            rtg_cfg['staticRouting']['defaultRoute']['gatewayAddress'] = dfgw
        except KeyError:
            rtg_cfg['staticRouting']['defaultRoute'] = {'gatewayAddress': dfgw, 'adminDistance': '1', 'mtu': '1500'}
    else:
        rtg_cfg['staticRouting']['defaultRoute'] = None

    cfg_result = client_session.update('routingConfigStatic', uri_parameters={'edgeId': esg_id},
                                       request_body_dict=rtg_cfg)
    if cfg_result['status'] == 204:
        return True
    else:
        return False


def get_firewall_state(client_session, esg_id):
    fw_state = client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': esg_id})['body']

    if fw_state['firewall']['enabled'] == 'false':
        return False
    elif fw_state['firewall']['enabled'] == 'true':
        return True
    else:
        return None


def set_firewall(client_session, esg_id, state):
    firewall_body = client_session.read('nsxEdgeFirewallConfig', uri_parameters={'edgeId': esg_id})['body']
    if state:
        firewall_body['firewall']['enabled'] = 'true'
    elif not state:
        firewall_body['firewall']['enabled'] = 'false'

    return client_session.update('nsxEdgeFirewallConfig', uri_parameters={'edgeId': esg_id},
                                 request_body_dict=firewall_body)


def params_check_ifaces(module):
    ifaces = module.params['interfaces']
    if not isinstance(ifaces, dict):
        module.fail_json(msg='Malformed Interfaces Dictionary: The Interfaces Information is not a dictionary')
    for iface_key, iface in ifaces.items():
        if not isinstance(iface, dict):
            module.fail_json(msg='Malformed Interface Dictionary: '
                                 'The Interface {} Information is not a dictionary'.format(iface_key))
        ip = iface.get('ip', None)
        pfx_len = iface.get('prefix_len', None)
        if_type = iface.get('iftype', None)
        lswitch = iface.get('logical_switch', None)
        portgroupid = iface.get('portgroup_id', None)
        if not (ip and pfx_len and if_type):
            module.fail_json(msg='You are missing one of the following parameter '
                                 'in the Interface Dict: ip or pfx_len or if_type')
        if not (lswitch or portgroupid):
            module.fail_json(msg='You are missing either: logical_switch or portgroup_id as '
                                 'parameters on {}'.format(iface_key))
        if (lswitch and portgroupid):
            module.fail_json(msg='Interface can either have: logical_switch or portgroup_id as parameters, '
                                 'but not both on {}'.format(iface_key))


def check_interfaces(client_session, esg_id, module):
    changed = None
    vnics = client_session.read('vnics', uri_parameters={'edgeId': esg_id})['body']
    ifaces = module.params['interfaces']

    params_check_ifaces(module)

    for vnic in vnics['vnics']['vnic']:
        vnic_deletion = None
        idx = 'vnic{}'.format(vnic['index'])

        if idx in ifaces:
            continue
        if 'portgroupId' in vnic:
            vnic_deletion = True
        if 'fence_param' in vnic:
            vnic_deletion = True
        if vnic['addressGroups']:
            vnic_deletion = True
        if vnic['name'] != idx:
            vnic_deletion = True

        if vnic_deletion:
            client_session.delete('vnic', uri_parameters={'edgeId': esg_id, 'index': vnic['index']})
            changed = True

    for vnic in vnics['vnics']['vnic']:
        vnic_changed = None
        idx = 'vnic{}'.format(vnic['index'])

        if idx not in ifaces:
            continue

        if vnic['name'] != ifaces[idx]['name']:
            vnic['name'] = ifaces[idx]['name']
            vnic_changed = True

        if vnic['type'] != ifaces[idx]['iftype']:
            vnic['type'] = ifaces[idx]['iftype']
            vnic_changed = True

        if 'portgroup_id' in ifaces[idx]:
            if not 'portgroupId' in vnic:
                vnic['portgroupId'] = ifaces[idx]['portgroup_id']
                vnic_changed = True
            else:
                if vnic['portgroupId'] != ifaces[idx]['portgroup_id']:
                    vnic['portgroupId'] = ifaces[idx]['portgroup_id']
                    vnic_changed = True
        elif 'logical_switch' in ifaces[idx]:
            lswitch_id = get_logical_switch(client_session, ifaces[idx]['logical_switch'])
            if not 'portgroupId' in vnic:
                vnic['portgroupId'] = lswitch_id
                vnic_changed = True
            else:
                if vnic['portgroupId'] != lswitch_id:
                    vnic['portgroupId'] = lswitch_id
                    vnic_changed = True

        if 'fence_param' in ifaces[idx]:
            fence_key, fence_val = ifaces[idx]['fence_param'].split('=')
            if not 'fenceParameter' in vnic:
                vnic['fenceParameter'] = {'key': fence_key,'value': fence_val}
                vnic_changed = True
            else:
                if vnic['fenceParameter']['key'] != fence_key or vnic['fenceParameter']['value'] != fence_val:
                    vnic['fenceParameter'] = {'key': fence_key,'value': fence_val}
                    vnic_changed = True

        if not vnic['addressGroups']:
            vnic['addressGroups'] = {'addressGroup': {'primaryAddress': ifaces[idx]['ip'],
                                     'subnetPrefixLength': ifaces[idx]['prefix_len']}}
            vnic_changed = True
        else:
            if vnic['addressGroups']['addressGroup']['primaryAddress'] != ifaces[idx]['ip']:
                vnic['addressGroups'] = {'addressGroup': {'primaryAddress': ifaces[idx]['ip'],
                                                          'subnetPrefixLength': str(ifaces[idx]['prefix_len'])}}
                vnic_changed = True
            elif vnic['addressGroups']['addressGroup']['subnetPrefixLength'] != str(ifaces[idx]['prefix_len']):
                vnic['addressGroups'] = {'addressGroup': {'primaryAddress': ifaces[idx]['ip'],
                                                          'subnetPrefixLength': str(ifaces[idx]['prefix_len'])}}
                vnic_changed = True

        if vnic_changed:
            vnic['isConnected'] = 'true'
            client_session.update('vnic', uri_parameters={'edgeId': esg_id, 'index': vnic['index']},
                                  request_body_dict={'vnic': vnic})
            changed = True

    return changed


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


def check_routes(client_session, esg_id, current_routes, module):
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
        rtg_config = client_session.read('routingConfigStatic', uri_parameters={'edgeId': esg_id})['body']
        rtg_config['staticRouting']['staticRoutes'] = {'route': new_routes}
        client_session.update('routingConfigStatic', uri_parameters={'edgeId': esg_id}, request_body_dict=rtg_config)

    return changed


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            name=dict(required=True),
            description=dict(),
            appliance_size=dict(default='Large', choices=['Compact', 'Large', 'X-Large', 'Quad Large']),
            resourcepool_moid=dict(required=True),
            datastore_moid=dict(required=True),
            datacenter_moid=dict(required=True),
            interfaces=dict(required=True, type='dict'),
            default_gateway=dict(),
            routes=dict(default=[], type='list'),
            username=dict(),
            password=dict(),
            remote_access=dict(default='false', choices=['true', 'false']),
            firewall=dict(default='true', choices=['true', 'false'])
        ),
        supports_check_mode=False
    )

    if module.params['remote_access'] == 'true' and not (module.params['password'] and module.params['username']):
        module.fail_json(msg='if remote access is enabled, username and password must be set')

    from nsxramlclient.client import NsxClient
    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                               module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'],
                               module.params['nsxmanager_spec']['password'])
    changed = False
    esg_create_response = {}
    esg_delete_response = {}
    edge_id, edge_params = get_edge(client_session, module.params['name'])

    if module.params['state'] == 'present':
        if not edge_id:
            edge_id, edge_params = create_edge_service_gateway(client_session, module)
            changed = True
    elif module.params['state'] == 'absent':
        if edge_id:
            esg_delete_response = delete_edge_service_gateway(client_session, edge_id)
            module.exit_json(changed=True, esg_create_response=esg_create_response,
                             esg_delete_response=esg_delete_response)
        else:
            module.exit_json(changed=False, esg_create_response=esg_create_response,
                             esg_delete_response=esg_delete_response)

    routes, current_dfgw = get_esg_routes(client_session, edge_id)
    fw_state = get_firewall_state(client_session, edge_id)
    ifaces_changed = check_interfaces(client_session, edge_id, module)
    routes_changed = check_routes(client_session, edge_id, routes, module)

    if ifaces_changed:
        changed = True
    if routes_changed:
        changed = True

    if module.params['default_gateway']:
        if current_dfgw != module.params['default_gateway']:
            changed = config_def_gw(client_session, edge_id, module.params['default_gateway'])
    else:
        if current_dfgw:
            changed = config_def_gw(client_session, edge_id, None)

    if module.params['firewall'] == 'false' and fw_state:
        set_firewall(client_session, edge_id, False)
        changed = True
    elif module.params['firewall'] == 'true' and not fw_state:
        set_firewall(client_session, edge_id, True)
        changed = True

    if changed:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
