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

__author__ = 'yfauser'


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


def check_ospf_state(current_config):
    if current_config['routing']['ospf']:
        if current_config['routing']['ospf']['enabled'] == 'true':
            return True
        else:
            return False
    else:
        return False


def set_ospf_state(current_config):
    if current_config['routing']['ospf']:
        if current_config['routing']['ospf']['enabled'] == 'false':
            current_config['routing']['ospf']['enabled'] = 'true'
            return True, current_config
        else:
            return False, current_config
    else:
        current_config['routing']['ospf']['enabled'] = 'true'
        return True, current_config


def check_router_id(current_config, router_id):
    current_router_id = current_config['routing']['routingGlobalConfig']['routerId']
    if current_router_id == router_id:
        return False, current_config
    else:
        current_config['routing']['routingGlobalConfig']['routerId'] = router_id
        return True, current_config


def check_ospf_options(current_config, graceful_restart, default_originate):
    changed = False
    current_ospf = current_config['routing']['ospf']
    c_grst_str = current_ospf.get('gracefulRestart', 'false')
    c_dio_str = current_ospf.get('defaultOriginate', 'false')

    if c_grst_str == 'true':
        c_grst = True
    else:
        c_grst = False

    if c_dio_str == 'true':
        c_dio = True
    else:
        c_dio = False

    if c_grst != graceful_restart and graceful_restart:
        current_config['routing']['ospf']['gracefulRestart'] = 'true'
        changed = True
    elif c_grst != graceful_restart and not graceful_restart:
        current_config['routing']['ospf']['gracefulRestart'] = 'false'
        changed = True

    if c_dio != default_originate and default_originate:
        current_config['routing']['ospf']['defaultOriginate'] = 'true'
        changed = True
    elif c_dio != default_originate and not default_originate:
        current_config['routing']['ospf']['defaultOriginate'] = 'false'
        changed = True

    return changed, current_config


def validate_areas(area_list):
    if area_list:
        for area in area_list:
            if not isinstance(area, dict):
                return False, 'Area {} is not a valid dictionary'.format(area)
            if not area.get('area_id'):
                return False, 'One Area in your list is missing the mandatory area_id parameter'
            if area.get('type') not in [None, 'normal', 'nssa']:
                return False, 'One Area has a wrong type, valid types are "normal" or "nssa"'
            if area.get('authentication') not in [None, 'none', 'password', 'md5']:
                return False, 'One Area has a wrong authentication type, valid types are "none", "password" and "md5"'
            elif area.get('authentication') in ['password', 'md5']:
                if not area.get('password'):
                    return False, 'One Area has authentication set, but no password specified'

    return True, None


def check_areas(client_session, current_config, d_area_list):
    changed = False
    new_areas = []
    if not d_area_list:
        d_area_list = []
    if current_config['routing']['ospf']['ospfAreas']:
        c_area_list = client_session.normalize_list_return(current_config['routing']['ospf']['ospfAreas']['ospfArea'])
    else:
        c_area_list = []

    # Filter out the Areas that are on NSX but not in the desired list, and check if the parameters are correct
    for c_area in c_area_list:
        for d_area in d_area_list:
            if c_area['areaId'] == str(d_area['area_id']):

                d_type = d_area.get('type', 'normal')
                if c_area['type'] != d_type:
                    c_area['type'] = d_type
                    changed = True

                c_auth = c_area.get('authentication')
                if c_auth:
                    c_auth_type = c_auth.get('type')
                    d_auth_type = d_area.get('authentication', 'none')
                    if c_auth_type != d_auth_type:
                        c_area['authentication']['type'] = d_auth_type
                        changed = True
                    if d_auth_type in ['password', 'md5']:
                        c_area['authentication']['value'] = d_area['password']
                        changed = True
                    else:
                        c_area['authentication']['value'] = None

                new_areas.append(c_area)
                break
        else:
            changed = True

    # Add the Areas that are in the desired list but not in NSX
    c_area_ids = [c_area['areaId'] for c_area in c_area_list]
    for d_area in d_area_list:
        if str(d_area['area_id']) not in c_area_ids:
            d_auth_type = d_area.get('authentication', 'none')
            d_type = d_area.get('type', 'normal')

            new_area = {'areaId': d_area['area_id'], 'type': d_type, 'authentication': {'type': d_auth_type}}

            if d_auth_type in ['password', 'md5']:
                new_area['authentication']['value'] = d_area['password']

            new_areas.append(new_area)

            changed = True

    if changed:
        current_config['routing']['ospf']['ospfAreas'] = {'ospfArea': new_areas}

    return changed, current_config


def get_current_config(client_session, edge_id):
    response = client_session.read('routingConfig', uri_parameters={'edgeId': edge_id})
    return response['body']


def update_config(client_session, current_config, edge_id):
    client_session.update('routingConfig', uri_parameters={'edgeId': edge_id},
                          request_body_dict=current_config)


def reset_config(client_session, edge_id):
    client_session.delete('routingOSPF', uri_parameters={'edgeId': edge_id})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            edge_name=dict(required=True, type='str'),
            router_id=dict(required=True, type='str'),
            graceful_restart=dict(default=True, type='bool'),
            default_originate=dict(default=False, type='bool'),
            logging=dict(default=False, type='bool'),
            log_level=dict(default='info', choices=['debug', 'info', 'notice', 'warning', 'error', 'critical',
                                                    'alert', 'emergency'], type='str'),
            areas=dict(type='list'),
            area_mapping=dict(type='list')
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    edge_id, edge_params = get_edge(client_session, module.params['edge_name'])
    if not edge_id:
        module.fail_json(msg='could not find Edge with name {}'.format(module.params['edge_name']))

    current_config = get_current_config(client_session, edge_id)

    if module.params['state'] == 'absent' and check_ospf_state(current_config):
        reset_config(client_session, edge_id)
        module.exit_json(changed=True, current_config=None)
    elif module.params['state'] == 'absent' and not check_ospf_state(current_config):
        module.exit_json(changed=False, current_config=None)

    changed_state, current_config = set_ospf_state(current_config)
    changed_rtid, current_config = check_router_id(current_config, module.params['router_id'])
    changed_opt, current_config = check_ospf_options(current_config, module.params['graceful_restart'],
                                                 module.params['default_originate'])

    valid, msg = validate_areas(module.params['areas'])
    if not valid:
        module.fail_json(msg=msg)

    changed_areas, current_config = check_areas(client_session, current_config, module.params['areas'])

    if (changed_state or changed_rtid or changed_opt or changed_areas):
        update_config(client_session, current_config, edge_id)
        module.exit_json(changed=True, current_config=current_config)
    else:
        module.exit_json(changed=False, current_config=current_config, areas=module.params['areas'])


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
