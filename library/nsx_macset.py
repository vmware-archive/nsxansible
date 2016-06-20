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


def get_macset_id(session, ms_name, scope):
    macsets = session.read('macsetScopeRead', uri_parameters={'scopeId': scope})['body']
    first_page = macsets['list']['macset']
    return [macset['objectId'] for macset in first_page if ms_name in macset['name']]


# Lookup macset information by ID
def get_macset_details(session, macset_id):
    return session.read('macset', uri_parameters={'macsetId': macset_id})['body']


# Create macset on specified scope
def create_macset(session, body_dict, scope_id):
    return session.create('macsetScopeCreate', uri_parameters={'scopeId': scope_id}, request_body_dict=body_dict)


def change_macset_details(session, macset_id, macset_details):
    revision = int(macset_details['macset']['revision'])
    revision += 1
    macset_details['macset']['revision'] = revision
    return session.update('macset', uri_parameters={'macsetId': macset_id}, request_body_dict=macset_details)


def delete_macset(session, macset_id):
    return session.delete('macset', uri_parameters={'macsetId': macset_id})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            name=dict(required=True),
            transportzone=dict(required=True),
            description=dict(),
            value=dict()
        ),
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])
    macset_id_lst = get_macset_id(client_session, module.params['name'], module.params['transportzone'])

    if len(macset_id_lst) is 0 and 'present' in module.params['state']:
        # Create a new macset
        new_macset = client_session.extract_resource_body_example('macsetScopeCreate', 'create')
        new_macset['macset']['name'] = module.params['name']
        new_macset['macset']['description'] = module.params['description']
        new_macset['macset']['value'] = module.params['value']
        create_response = create_macset(client_session, new_macset, module.params['transportzone'])
        module.exit_json(changed=True, argument_spec=module.params, create_response=create_response)
    elif len(macset_id_lst) is not 0 and 'present' in module.params['state']:
        # Update existing macset
        macset_details = get_macset_details(client_session, macset_id_lst[0])
        change_required = False
        for detail_key, detail_val in macset_details['macset'].iteritems():
            if detail_key == 'description' and detail_val != module.params['description']:
                macset_details['macset']['description'] = module.params['description']
                change_required = True
            elif detail_key == 'value' and detail_val != module.params['value']:
                macset_details['macset']['value'] = module.params['value']
                change_required = True
        if change_required:
            ms_ops_response = change_macset_details(client_session, macset_id_lst[0], macset_details)
            module.exit_json(changed=True, argument_spec=module.params, ms_ops_response=ms_ops_response)
        else:
            module.exit_json(changed=False, argument_spec=module.params)
    elif len(macset_id_lst) is not 0 and 'absent' in module.params['state']:
        # Delete existing macset
        ms_ops_response = delete_macset(client_session, macset_id_lst[0])
        module.exit_json(changed=True, argument_spec=module.params, ms_ops_response=ms_ops_response)
    else:
        module.exit_json(changed=False, argument_spec=module.params)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
