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


def validate_prefixes(prefix_list):
    if not prefix_list:
        return True, None

    for prefix in prefix_list:
        if not isinstance(prefix, dict):
            return False, 'prefix {} is not a valid dictionary'.format(prefix)
        prefix_name = prefix.get('name')
        prefix_network = prefix.get('network')

        if not prefix_name:
            return False, 'prefix {} is missing the mandatory name attribute'.format(prefix)
        if not prefix_network:
            return False, 'prefix {} is missing the mandatory network attribute'.format(prefix)

    return True, None


def check_prefixes(client_session, routing_cfg, d_prefix_list):
    changed = False
    new_prefixes = []

    if not d_prefix_list:
        d_prefix_list = []

    if routing_cfg['routing']['routingGlobalConfig'].get('ipPrefixes'):
        prefixes_from_api = routing_cfg['routing']['routingGlobalConfig']['ipPrefixes'].get('ipPrefix')
        c_prefix_list = client_session.normalize_list_return(prefixes_from_api)
    else:
        c_prefix_list = []

    # Filter out the Prefixes that are on NSX but not in the desired list
    for c_prefix in c_prefix_list:
        for d_prefix in d_prefix_list:
            if c_prefix['name'] == d_prefix['name']:

                if c_prefix['ipAddress'] != d_prefix['network']:
                    c_prefix['ipAddress'] = d_prefix['network']
                    changed = True

                new_prefixes.append(c_prefix)
                break
        else:
            changed = True

    # Add the Prefixes that are in the desired list but not in NSX
    c_prefix_names = [c_prefix['name'] for c_prefix in c_prefix_list]
    for d_prefix in d_prefix_list:
        if d_prefix['name'] not in c_prefix_names:
            new_prefix = {'name': d_prefix['name'], 'ipAddress': d_prefix['network']}
            new_prefixes.append(new_prefix)
            changed = True

    if changed:
        routing_cfg['routing']['routingGlobalConfig']['ipPrefixes'] = {'ipPrefix': new_prefixes}

    return changed, routing_cfg


def normalize_rules(rule_list):
    rule_list_ret = []
    if not rule_list:
        return True, None, rule_list_ret

    for rule in rule_list:
        if not isinstance(rule, dict):
            return False, 'rule {} is not a valid dictionary'.format(rule), None

        rule_learner = rule.get('learner')
        if rule_learner not in ['bgp', 'ospf']:
            return False, 'rule {} has a wrong learner type. Valid types are bgp or ospf'.format(rule), None

        rule_priority = rule.get('priority', 'missing')
        if rule_priority == 'missing':
            return False, 'rule {} is missing the mandatory priority value'.format(rule), None
        rule_priority = str(rule.get('priority'))

        rule_static = rule.get('static', 'false')
        if isinstance(rule_static, bool):
            rule_static = str(rule_static).lower()
        elif rule_static not in ['true', 'false']:
            return False, 'rule {}: Static must be either true or false'.format(rule), None

        rule_connected = rule.get('connected', 'false')
        if isinstance(rule_connected, bool):
            rule_connected = str(rule_connected).lower()
        elif rule_connected not in ['true', 'false']:
            return False, 'rule {}: connected must be either true or false'.format(rule), None

        rule_bgp = rule.get('bgp', 'false')
        if isinstance(rule_bgp, bool):
            rule_bgp = str(rule_bgp).lower()
        elif rule_bgp not in ['true', 'false']:
            return False, 'rule {}: bgp must be either true or false'.format(rule), None

        rule_ospf = rule.get('ospf', 'false')
        if isinstance(rule_ospf, bool):
            rule_ospf = str(rule_ospf).lower()
        elif rule_ospf not in ['true', 'false']:
            return False, 'rule {}: ospf must be either true or false'.format(rule), None

        rule_prefix = rule.get('prefix')

        rule_action = rule.get('action', 'permit')
        if rule_action not in ['permit', 'deny']:
            return False, 'rule {}: action must be either permit or deny'.format(rule), None

        rule_list_ret.append({'learner': rule_learner, 'priority': rule_priority, 'static': rule_static,
                              'connected': rule_connected, 'bgp': rule_bgp, 'ospf': rule_ospf, 'prefix': rule_prefix,
                              'action': rule_action})

    return True, None, rule_list_ret


def check_rules(client_session, routing_cfg, d_rule_list, protocol):
    changed = None
    new_rules = []

    if not d_rule_list:
        d_rule_list = []

    conf = routing_cfg['routing'].get(protocol)

    if conf:
        if conf['redistribution']['rules']:
            rules_from_api = conf['redistribution']['rules'].get('rule')
            c_rules_list = client_session.normalize_list_return(rules_from_api)
        else:
            c_rules_list = []
    else:
        c_rules_list = []

    # Filter out the Rules that are on NSX but not in the desired list
    for c_rule in c_rules_list:
        for d_rule in d_rule_list:
            if d_rule['learner'] == protocol:
                if c_rule['id'] == d_rule['priority']:
                    if c_rule.get('prefixName') != d_rule['prefix']:
                        c_rule['prefixName'] = d_rule['prefix']
                        changed = True

                    if c_rule.get('action') != d_rule['action']:
                        c_rule['action'] = d_rule['action']
                        changed = True

                    if c_rule['from'].get('ospf') != d_rule['ospf']:
                        c_rule['from']['ospf'] = d_rule['ospf']
                        changed = True

                    if c_rule['from'].get('bgp') != d_rule['bgp']:
                        c_rule['from']['bgp'] = d_rule['bgp']
                        changed = True

                    if c_rule['from'].get('connected') != d_rule['connected']:
                        c_rule['from']['connected'] = d_rule['connected']
                        changed = True

                    if c_rule['from'].get('static') != d_rule['static']:
                        c_rule['from']['static'] = d_rule['static']
                        changed = True

                    new_rules.append(c_rule)
                    break
        else:
            changed = True

    # Add the Rules that are in the desired list but not in NSX
    c_rule_ids = [c_rule['id'] for c_rule in c_rules_list]
    for d_rule in d_rule_list:
        if d_rule['learner'] == protocol:
            if d_rule['priority'] not in c_rule_ids:
                new_rule = {'id': d_rule['priority'], 'action': d_rule['action'],
                            'from': {'ospf': d_rule['ospf'], 'bgp': d_rule['bgp'],
                                     'connected': d_rule['connected'], 'static': d_rule['static']}}
                if d_rule['prefix']:
                    new_rule['prefixName'] = d_rule['prefix']

                new_rules.append(new_rule)
                changed = True

    if changed:
        routing_cfg['routing'][protocol]['redistribution']['rules'] = {'rule': new_rules}

    return changed, routing_cfg


def check_state(routing_cfg, protocol):
    conf = routing_cfg['routing'].get(protocol)
    if conf:
        if conf['redistribution']['enabled'] == 'true':
            return True
        else:
            return False
    else:
        return False


def set_state(routing_cfg, protocol):
    conf = routing_cfg['routing'].get(protocol)
    if conf:
        if conf['redistribution']['enabled'] == 'false':
            routing_cfg['routing'][protocol]['redistribution']['enabled'] = 'true'
            return routing_cfg
        else:
            return routing_cfg
    else:
        routing_cfg['routing'][protocol] = {'redistribution': {'enabled': 'true'}}
        return routing_cfg


def reset_config(routing_cfg, protocol):
    routing_cfg['routing'][protocol]['redistribution'] = {'enabled': 'false', 'rules': None}
    return routing_cfg


def update_config(client_session, current_config, edge_id):
    client_session.update('routingConfig', uri_parameters={'edgeId': edge_id},
                          request_body_dict=current_config)


def get_current_config(client_session, edge_id):
    response = client_session.read('routingConfig', uri_parameters={'edgeId': edge_id})
    return response['body']


def main():
    module = AnsibleModule(
        argument_spec=dict(
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            edge_name=dict(required=True, type='str'),
            ospf_state=dict(required=True, choices=['present', 'absent'], type='str'),
            bgp_state=dict(required=True, choices=['present', 'absent'], type='str'),
            prefixes=dict(type='list'),
            rules=dict(type='list')
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

    state_changed = False
    for protocol in ['ospf', 'bgp']:
        state_val = '{}_state'.format(protocol)
        if module.params[state_val] == 'absent' and check_state(current_config, protocol):
            current_config = reset_config(current_config, protocol)
            state_changed = True
        elif module.params[state_val] == 'present' and not check_state(current_config, protocol):
            current_config = set_state(current_config, protocol)
            state_changed = True

    valid, msg = validate_prefixes(module.params['prefixes'])
    if not valid:
        module.fail_json(msg=msg)

    prefixes_changed, current_config = check_prefixes(client_session, current_config, module.params['prefixes'])

    valid, msg, rules_list = normalize_rules(module.params['rules'])
    if not valid:
        module.fail_json(msg=msg)

    rules_changed = {'ospf': None, 'bgp': None}
    for protocol in ['ospf', 'bgp']:
        state_val = '{}_state'.format(protocol)
        if module.params[state_val] == 'present':
            rules_changed[protocol], current_config = check_rules(client_session, current_config, rules_list, protocol)

    if state_changed or prefixes_changed or rules_changed['bgp'] or rules_changed['ospf']:
        update_config(client_session, current_config, edge_id)
        module.exit_json(changed=True, current_config=current_config)
    else:
        module.exit_json(changed=False, current_config=current_config)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()