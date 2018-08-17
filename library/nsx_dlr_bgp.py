#!/usr/bin/env python
#coding=utf-8

__author__ = "matt.pinizzotto@wwt.com"


def get_edge(client_session, edge_name):
    all_edge = client_session.read_all_pages('nsxEdges', 'read')
    try:
        edge_params = [scope for scope in all_edge if scope['name'] == edge_name][0]
        edge_id = edge_params['objectId']
    except IndexError:
        return None, None

    return edge_id, edge_params

def check_bgp_state(current_config):
    if 'bgp' in current_config['routing']:
        if current_config['routing']['bgp']['enabled'] == 'true':
            return True
        else:
            return False
    else:
        return False

def set_bgp_state(current_config, resource_body):
    if 'bgp' in current_config['routing']:
        if current_config['routing']['bgp']['enabled'] == 'false':
            resource_body['bgp']['enabled'] = 'true'
            return True, resource_body
        else:
            resource_body['bgp']['enabled'] = 'true'
            return True, resource_body
    else:
        resource_body['bgp']['enabled'] = 'true'
        return True, resource_body

def check_bgp_as(current_config, resource_body, localas):
    changed = False

    if 'bgp' in current_config['routing']:
        current_bgp = current_config['routing']['bgp']
        c_localas = current_bgp.get('localAS')

        if c_localas != localas:
            resource_body['bgp']['localAS'] = localas
            changed = True
            return changed, resource_body

        else:
           resource_body['bgp']['localAS'] = c_localas
           changed = False
           return changed, resource_body

    else:
        resource_body['bgp']['localAS'] = localas
        changed = True

        return changed, resource_body


def check_router_id(current_config, router_id):
    current_routing_cfg = current_config['routing']['routingGlobalConfig']
    current_router_id = current_routing_cfg.get('routerId', None)

    if current_router_id == router_id:
        return False, current_config
    else:
        current_config['routing']['routingGlobalConfig']['routerId'] = router_id
        return True, current_config

def check_ecmp(current_config, ecmp):
    current_ecmp_cfg = current_config['routing']['routingGlobalConfig']
    current_ecmp_state = current_ecmp_cfg.get('ecmp', None)

    if current_ecmp_state == ecmp:
        return False, current_config
    else:
        current_config['routing']['routingGlobalConfig']['ecmp'] = ecmp
        return True, current_config


def check_bgp_options(current_config, resource_body, graceful_restart):
    changed = False

    if 'bgp' in current_config['routing']:
        current_bgp = current_config['routing']['bgp']
        c_grst_str = current_bgp.get('gracefulRestart', 'false')

        if c_grst_str == 'true':
            c_grst = True
        else:
            c_grst = False

        if c_grst != graceful_restart and graceful_restart:
            resource_body['bgp']['gracefulRestart'] = 'true'
            changed = True
        elif c_grst != graceful_restart and not graceful_restart:
            resource_body['bgp']['gracefulRestart'] = 'false'
            changed = True

        return changed, resource_body

    else:
        resource_body['bgp']['gracefulRestart'] = graceful_restart
        changed = True

        return changed, resource_body


def normalize_neighbor_list(neighbor_list):
    new_neighbor_list = []

    if neighbor_list:
        for neighbor in neighbor_list:

            if not isinstance(neighbor, dict):
                return False, 'neighbor_list {} is not a valid dictionary'.format(neighbor)

            if neighbor.get('ipAddress', 'missing') == 'missing':
                return False, 'neighbor list entry {} in your list is missing the mandatory ipAddress parameter'.format(neighbor.get('ipAddress', None))
            else:
                neighbor['ipAddress'] = str(neighbor['ipAddress'])

            if neighbor.get('remoteAS', 'missing') == 'missing':
                return False, 'neighbor list entry {} in your list is missing the mandatory remoteAS parameter'.format(neighbor.get('remoteAS', None))
            else:
                neighbor['remoteAS'] = str(neighbor['remoteAS'])

            if neighbor.get('protocolAddress', 'missing') == 'missing':
                return False, 'neighbor list entry {} in your list is missing the mandatory protocolAddress parameter'.format(neighbor.get('protocolAddress', None))
            else:
                neighbor['protocolAddress'] = str(neighbor['protocolAddress'])

            if neighbor.get('forwardingAddress', 'missing') == 'missing':
                return False, 'neighbor list entry {} in your list is missing the mandatory forwardingAddress parameter'.format(neighbor.get('forwardingAddress', None))
            else:
                neighbor['forwardingAddress'] = str(neighbor['forwardingAddress'])

            if neighbor.get('bgpFilters', 'missing') == 'missing':
                neighbor['bgpFilters'] = None
            else:
                pass

            if neighbor.get('holdDownTimer', 'missing') == 'missing':
                neighbor['holdDownTimer'] = '180'
            else:
                neighbor['holdDownTimer'] = str(neighbor['holdDownTimer'])

            if neighbor.get('weight', 'missing') == 'missing':
                neighbor['weight'] = '60'

            else:
                neighbor['weight'] = str(neighbor['weight'])

            if neighbor.get('remoteASNumber', 'missing') == 'missing':
                neighbor['remoteASNumber'] = neighbor['remoteAS']

            else:
                neighbor['remoteASNumber'] = str(neighbor['remoteASNumber'])

            if neighbor.get('keepAliveTimer', 'missing') == 'missing':
                neighbor['keepAliveTimer'] = '60'

            else:
                neighbor['keepAliveTimer'] = str(neighbor['keepAliveTimer'])
            new_neighbor_list.append(neighbor)

    return True, None, new_neighbor_list


def check_bgp_neighbors(client_session, current_config, resource_body, bgp_neighbors):
    changed = False

    if 'bgp' in current_config['routing']:
        if current_config['routing']['bgp']['bgpneighbors']:
            c_neighbor_list = client_session.normalize_list_return(current_config['routing']['bgp']['bgpneighbors']['bgpneighbor'])
        else:
            c_neighbor_list = []

        for items in bgp_neighbors:
            if not items in c_neighbor_list:
                c_neighbor_list.append(items)

        resource_body['bgp']['bgpneighbors'] = {'bgpneighbor': c_neighbor_list}
        changed = True

        return changed, current_config, resource_body

    else:
        c_neighbor_list = []

        for new_neighbor in bgp_neighbors:
            c_neighbor_list.append(new_neighbor)

        resource_body['bgp']['bgpneighbors'] = {'bgpneighbor': c_neighbor_list}
        changed = True

        return changed, current_config, resource_body


def get_current_config(client_session, edge_id):
    response = client_session.read('routingConfig', uri_parameters={'edgeId': edge_id})
    return response['body']


def get_resource_body(client_session):
    response = client_session.extract_resource_body_example('routingBGP', 'update')
    return response


def update_config(client_session, current_config, edge_id):
    client_session.update('routingConfig', uri_parameters={'edgeId': edge_id},
                          request_body_dict=current_config)


def update_config_bgp(client_session, resource_body, edge_id):
    client_session.update('routingBGP', uri_parameters={'edgeId': edge_id}, request_body_dict=resource_body)


def reset_config(client_session, edge_id):
    client_session.delete('routingConfig', uri_parameters={'edgeId': edge_id})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            edge_name=dict(required=True, type='str'),
            graceful_restart=dict(default=True, type='bool'),
            router_id=dict(required=True, type='str'),
            ecmp=dict(default='false', choices=['true', 'false']),
            localas=dict(required=True, type='str'),
            bgp_neighbors=dict(required=True, type='list'),
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
    resource_body = get_resource_body(client_session)

    if module.params['state'] == 'absent' and check_bgp_state(current_config):
        reset_config(client_session, edge_id)
        module.exit_json(changed=True, current_config=None)

    elif module.params['state'] == 'absent' and not check_bgp_state(current_config):
        module.exit_json(changed=False, current_config=None)

    changed_state, resource_body = set_bgp_state(current_config, resource_body)
    changed_as, resource_body = check_bgp_as(current_config, resource_body, module.params['localas'])
    changed_opt, resource_body = check_bgp_options(current_config, resource_body, module.params['graceful_restart'])
    changed_ecmp, current_config = check_ecmp(current_config, module.params['ecmp'])
    changed_rtid, current_config = check_router_id(current_config, module.params['router_id'])

    valid, msg, neighbor_list = normalize_neighbor_list(module.params['bgp_neighbors'])
    if not valid:
	      module.fail_json(msg=msg)

    changed_neighbors, current_config, resource_body = check_bgp_neighbors(client_session, current_config, resource_body, neighbor_list)

    if (changed_state or changed_as or changed_opt or changed_neighbors or changed_rtid or changed_ecmp):
        update_config(client_session, current_config, edge_id)
        update_config_bgp(client_session, resource_body, edge_id)
        module.exit_json(changed=True, current_config=current_config, resource_body=resource_body)
    else:
        module.exit_json(changed=False, current_config=current_config, resource_body=resource_body)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
