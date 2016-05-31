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


def retrieve_scope(session, tz_name):
    vdn_scopes = session.read('vdnScopes', 'read')['body']
    vdn_scope_dict_list = vdn_scopes['vdnScopes']['vdnScope']
    if isinstance(vdn_scope_dict_list, dict):
        if vdn_scope_dict_list['name'] == tz_name:
            return vdn_scope_dict_list['objectId']
    elif isinstance(vdn_scope_dict_list, list):
        return [scope['objectId'] for scope in vdn_scope_dict_list if scope['name'] == tz_name][0]


def get_lswitch_id(session, lswitchname, scope):
    tz_lswitches=session.read('logicalSwitches', uri_parameters={'scopeId': scope})['body']
    try:
        first_page=tz_lswitches['virtualWires']['dataPage']['virtualWire']
    except KeyError:
        return []
    if isinstance(first_page, dict) and lswitchname in first_page['name']:
        return [first_page['objectId']]
    elif isinstance(first_page, list):
        return [lswitch['objectId'] for lswitch in first_page if lswitchname in lswitch['name']]
    return []


def get_lswitch_details(session, lswitch_id):
    return session.read('logicalSwitch', uri_parameters={'virtualWireID': lswitch_id})['body']


def create_lswitch(session, lswitchname, lswitchdesc, lswitchcpmode, scope):
    lswitch_create_dict = session.extract_resource_body_schema('logicalSwitches', 'create')
    lswitch_create_dict['virtualWireCreateSpec']['controlPlaneMode'] = lswitchcpmode
    lswitch_create_dict['virtualWireCreateSpec']['name'] = lswitchname
    lswitch_create_dict['virtualWireCreateSpec']['description'] = lswitchdesc
    lswitch_create_dict['virtualWireCreateSpec']['tenantId'] = 'Unused'
    return  session.create('logicalSwitches', uri_parameters={'scopeId': scope}, request_body_dict=lswitch_create_dict)


def change_lswitch_details(session, lswitchid, body_dict):
    return session.update('logicalSwitch', uri_parameters={'virtualWireID': lswitchid}, request_body_dict=body_dict)


def delete_lswitch(session, lswitchid):
    return session.delete('logicalSwitch', uri_parameters={'virtualWireID': lswitchid})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True),
            name=dict(required=True),
            description=dict(),
            transportzone=dict(required=True),
            controlplanemode=dict(default='UNICAST_MODE', choices=['UNICAST_MODE', 'MULTICAST_MODE', 'HYBRID_MODE'])
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    vdn_scope=retrieve_scope(client_session, module.params['transportzone'])
    lswitch_id=get_lswitch_id(client_session, module.params['name'], vdn_scope)

    if len(lswitch_id) is 0 and 'present' in module.params['state']:
        ls_ops_response=create_lswitch(client_session, module.params['name'], module.params['description'],
                                       module.params['controlplanemode'], vdn_scope)
        module.exit_json(changed=True, argument_spec=module.params, ls_ops_response=ls_ops_response)
    elif len(lswitch_id) is not 0 and 'present' in module.params['state']:
        lswitch_details=get_lswitch_details(client_session,lswitch_id[0])
        change_required=False
        for lswitch_detail_key, lswitch_detail_value in lswitch_details['virtualWire'].iteritems():
            if lswitch_detail_key == 'name' and lswitch_detail_value != module.params['name']:
                #TODO: Check the bellow line
                lswitch_details['virtualWire']['name']=module.params['nsxmanager_spec']['name']
                change_required=True
            elif lswitch_detail_key == 'description' and lswitch_detail_value != module.params['description']:
                lswitch_details['virtualWire']['description']=module.params['description']
                change_required=True
            elif lswitch_detail_key == 'controlPlaneMode' and lswitch_detail_value != module.params['controlplanemode']:
                lswitch_details['virtualWire']['controlPlaneMode']=module.params['controlplanemode']
                change_required=True
        if change_required:
            ls_ops_response=change_lswitch_details(client_session,lswitch_id[0],lswitch_details)
            module.exit_json(changed=True, argument_spec=module.params, ls_ops_response=ls_ops_response)
        else:
            module.exit_json(changed=False, argument_spec=module.params)
    elif len(lswitch_id) is not 0 and 'absent' in module.params['state']:
        ls_ops_response=delete_lswitch(client_session, lswitch_id[0])
        module.exit_json(changed=True, argument_spec=module.params, ls_ops_response=ls_ops_response)
    else:
        module.exit_json(changed=False, argument_spec=module.params)



from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
