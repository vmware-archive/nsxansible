#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2015 VMware, Inc. All Rights Reserved.
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


def retrieve_scope(session, tz_name):
    vdn_scopes = session.read('vdnScopes', 'read')['body']
    try:
        vdn_scope_dict_list = vdn_scopes['vdnScopes']['vdnScope']
    except TypeError:
        return None
    if isinstance(vdn_scope_dict_list, dict):
        if vdn_scope_dict_list['name'] == tz_name:
            return vdn_scope_dict_list['objectId']
    elif isinstance(vdn_scope_dict_list, list):
        return [scope['objectId'] for scope in vdn_scope_dict_list if scope['name'] == tz_name][0]


def get_vdnscope_properties(session, vdn_scope):
    vdnscope_properties = {'name': None, 'description': None, 'controlplanemode': None, 'cluster_moid_list': []}
    vdn_scope_content = session.read('vdnScope', uri_parameters={'scopeId': vdn_scope})['body']['vdnScope']

    vdnscope_properties['name'] = vdn_scope_content.get('name')
    vdnscope_properties['description'] = vdn_scope_content.get('description')
    vdnscope_properties['controlplanemode'] = vdn_scope_content.get('controlPlaneMode')

    if isinstance(vdn_scope_content['clusters']['cluster'], dict):
        single_cluster_moid = vdn_scope_content['clusters']['cluster']['cluster']['objectId']
        vdnscope_properties['cluster_moid_list'].append(single_cluster_moid)
    elif isinstance(vdn_scope_content['clusters']['cluster'], list):
        for cluster in vdn_scope_content['clusters']['cluster']:
            vdnscope_properties['cluster_moid_list'].append(cluster['cluster']['objectId'])

    return vdnscope_properties


def check_scope_states(session, tz_name):
    if not retrieve_scope(session, tz_name):
        return 'absent'
    else:
        return 'present'


def state_delete_scope(session, module):
    vdn_scope = retrieve_scope(session, module.params['name'])
    if not module.check_mode:
        session.delete('vdnScope', uri_parameters={'scopeId': vdn_scope})
    module.exit_json(changed=True)


def state_create_scope(session, module):
    vdn_create_spec = session.extract_resource_body_example('vdnScopes', 'create')
    vdn_create_spec['vdnScope']['clusters']['cluster']['cluster']['objectId'] = module.params['cluster_moid_list'][0]
    vdn_create_spec['vdnScope']['name'] = module.params['name']
    vdn_create_spec['vdnScope']['description'] = module.params['description']
    vdn_create_spec['vdnScope']['controlPlaneMode'] = module.params['controlplanemode']

    if not module.check_mode:
        vdn_scope = session.create('vdnScopes', request_body_dict=vdn_create_spec)['objectId']
        if len(module.params['cluster_moid_list']) > 1:
            change_member_clusters(session, vdn_scope, module.params['cluster_moid_list'][1:], 'expand')
        module.exit_json(changed=True, vdn_scope=vdn_scope)
    else:
        module.exit_json(changed=True)


def update_vdnscope_attributes(session, vdn_scope, module):
    vdn_update_spec = session.extract_resource_body_example('vdnScopeAttribUpdate', 'update')
    vdn_update_spec['vdnScope']['name'] = module.params['name']
    vdn_update_spec['vdnScope']['description'] = module.params['description']
    vdn_update_spec['vdnScope']['objectId'] = vdn_scope
    vdn_update_spec['vdnScope']['controlPlaneMode'] = module.params['controlplanemode']
    return session.update('vdnScopeAttribUpdate', uri_parameters={'scopeId': vdn_scope},
                          request_body_dict=vdn_update_spec)


def change_member_clusters(session, vdn_scope_id, cluster_list, action):
    return_list = []
    for cluster in cluster_list:
        vdn_edit_spec = session.extract_resource_body_example('vdnScope', 'create')
        vdn_edit_spec['vdnScope']['objectId'] = vdn_scope_id
        vdn_edit_spec['vdnScope']['clusters']['cluster']['cluster']['objectId'] = cluster
        update_response = session.create('vdnScope', uri_parameters={'scopeId': vdn_scope_id},
                                         query_parameters_dict={'action': action},
                                         request_body_dict=vdn_edit_spec)
        return_list.append(update_response)

    return return_list


def scope_cluster_change(session, vdn_scope_id, module, cluster_list):
    if set(module.params['cluster_moid_list']) - set(cluster_list):
        return change_member_clusters(session, vdn_scope_id,
                                      set(module.params['cluster_moid_list']) - set(cluster_list), 'expand')
    elif set(cluster_list) - set(module.params['cluster_moid_list']):
        return change_member_clusters(session, vdn_scope_id,
                                      set(cluster_list) - set(module.params['cluster_moid_list']), 'shrink')


def state_check_scope_update(session, module):
    vdn_scope_id = retrieve_scope(session, module.params['name'])
    vdn_props = get_vdnscope_properties(session, vdn_scope_id)
    changed_property = False
    changed_cluster_list = False

    for property_key in vdn_props.keys():
        if property_key == 'cluster_moid_list':
            if set(vdn_props['cluster_moid_list']) != set(module.params[property_key]):
                changed_cluster_list = True

        elif vdn_props[property_key] != module.params[property_key]:
            changed_property = True

    if changed_cluster_list:
        if not module.check_mode:
            scope_cluster_change(session, vdn_scope_id, module, vdn_props['cluster_moid_list'])

    if changed_property:
        if not module.check_mode:
            update_vdnscope_attributes(session, vdn_scope_id, module)

    if changed_cluster_list or changed_property:
        module.exit_json(changed=True, vdn_props=vdn_props)


def state_exit_unchanged(session, module):
    module.exit_json(changed=False)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            name=dict(required=True, type='str'),
            description=dict(type='str'),
            controlplanemode=dict(default='UNICAST_MODE',
                                  choices=['HYBRID_MODE', 'MULTICAST_MODE', 'UNICAST_MODE'],
                                  type='str'),
            cluster_moid_list=dict(required=True, type='list')
        ),
        supports_check_mode=True
    )

    from nsxramlclient.client import NsxClient

    s = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                  module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    scope_state = {'absent':
                       {'absent': state_exit_unchanged,
                        'present': state_delete_scope},
                   'present':
                       {'absent': state_create_scope,
                        'present': state_check_scope_update}
                   }
    scope_state[module.params['state']][check_scope_states(s, module.params['name'])](s, module)

    module.exit_json(changed=False)


from ansible.module_utils.basic import *


if __name__ == '__main__':
    main()
