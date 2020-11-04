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

def params_check_iface(module):
    iface = module.params['interface']
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

def check_interface(client_session, dlr_id, module):
    changed = None
    params_check_iface(module)

    intfs_api = client_session.read('interfaces', uri_parameters={'edgeId': dlr_id})['body']

    if intfs_api['interfaces']:
        intfs = client_session.normalize_list_return(intfs_api['interfaces']['interface'])
    else:
        intfs = []

    current_interfaces = intfs
    intfs_namedict = {intf['name']: intf for intf in intfs}

    iface = module.params['interface']
    iface_exists = iface['name'] in intfs_namedict.keys()

    if iface_exists:
        intf = intfs_namedict[iface['name']]
        if module.params['state'] == 'absent':
            client_session.delete('interface', uri_parameters={'edgeId': dlr_id, 'index': intf['index']})
            changed = True
        elif module.params['state'] == 'present':
            intf_changed = None
            ifindex = intf['index']

            if intf['type'] != iface['iftype']:
                intf['type'] = iface['iftype']
                intf_changed = True

            if 'portgroup_id' in iface:
                if not 'connectedToId' in intf:
                    intf['connectedToId'] = iface['portgroup_id']
                    intf_changed = True
                else:
                    if intf['connectedToId'] != iface['portgroup_id']:
                        intf['connectedToId'] = iface['portgroup_id']
                        intf_changed = True
            elif 'logical_switch' in iface:
                lswitch_id = get_logical_switch(client_session, iface['logical_switch'])
                if not 'connectedToId' in intf:
                    intf['connectedToId'] = lswitch_id
                    intf_changed = True
                else:
                    if intf['connectedToId'] != lswitch_id:
                        intf['connectedToId'] = lswitch_id
                        intf_changed = True

            if not intf['addressGroups']:
                intf['addressGroups'] = {'addressGroup': {'primaryAddress': iface['ip'],
                                        'subnetPrefixLength': iface['prefix_len']}}
                intf_changed = True
            else:
                if intf['addressGroups']['addressGroup']['primaryAddress'] != iface['ip']:
                    intf['addressGroups'] = {'addressGroup': {'primaryAddress': iface['ip'],
                                                            'subnetPrefixLength': str(iface['prefix_len'])}}
                    intf_changed = True
                elif intf['addressGroups']['addressGroup']['subnetPrefixLength'] != str(iface['prefix_len']):
                    intf['addressGroups'] = {'addressGroup': {'primaryAddress': iface['ip'],
                                                            'subnetPrefixLength': str(iface['prefix_len'])}}
                    intf_changed = True

            if intf_changed:
                intf['isConnected'] = 'true'
                intfs_update =  {'interface': intf}
                client_session.update('interface', uri_parameters={'edgeId': dlr_id, 'index': ifindex},
                                      request_body_dict=intfs_update)
                changed = True
    elif module.params['state'] == 'present':
        connected_to = None
        if 'portgroup_id' in iface:
            connected_to = iface['portgroup_id']
        elif 'logical_switch' in iface:
            lswitch_id = get_logical_switch(client_session, iface['logical_switch'])
            connected_to = lswitch_id
        add_if = {'name': iface['name'], 'type': iface['iftype'], 'isConnected': "True",
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
            interface=dict(required=True, type='dict'),
            username=dict(),
            password=dict(),
            remote_access=dict(default='false', choices=['true', 'false'])
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
    dlr_id, dlr_params = get_dlr(client_session, module.params['name'])
    if dlr_id is None:
        module.fail_json(msg='{} dlr not found'.format(module.params['name']))

    ifaces_changed, current_interfaces = check_interface(client_session, dlr_id, module)

    module.exit_json(changed=ifaces_changed, interfaces=current_interfaces)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
