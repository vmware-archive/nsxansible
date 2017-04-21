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

def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            name=dict(required=True),
            description=dict(),
            rules=dict(type='list'),
            section_type=dict(required=True, choices=['L2', 'L3', 'L3R'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec, 
        supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient
    client_session=NsxClient(module.params['nsxmanager_spec']['raml_file'], 
                             module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'], 
                             module.params['nsxmanager_spec']['password'])

    l2_section_list, l3r_section_list, l3_section_list, detailed_dfw_sections = dfw_section_list(client_session)

    dfw_section_name = module.params['name']
    dfw_section_type = module.params['section_type']

    if 'present' in module.params['state']:

        vccontent = connect_to_api(module)

        rules_schema = []
        for rule in module.params['rules']:
            rule['section'] = dfw_section_name
            rule['section_type'] = dfw_section_type
            result, dfw_params = dfw_rule_parse(client_session, rule, l2_section_list, l3r_section_list, l3_section_list)
            if not result:
                module.fail_json(msg=dfw_params)
            rule_schema = dfw_rule_construct(client_session, dfw_params, vccontent)
            rules_schema.append(rule_schema)
    
        if dfw_section_type == 'L2':
            for val in l2_section_list:
                if dfw_section_name in val:
                    # Section with the same name already exist
                    dfw_section_id = str(val[1])
                    response = dfw_section_update(client_session, 
                                  dfw_section_id, dfw_section_name, 
                                  dfw_section_type, rules_schema)
                    module.exit_json(changed=False, argument_spec=module.params)
        elif dfw_section_type == 'L3':
            for val in l3_section_list:
                if dfw_section_name in val:
                    # Section with the same name already exist
                    dfw_section_id = str(val[1])
                    response = dfw_section_update(client_session, 
                                  dfw_section_id, dfw_section_name, 
                                  dfw_section_type, rules_schema)
                    module.exit_json(changed=False, argument_spec=module.params)
        elif dfw_section_type == 'L3R':
            for val in l3r_section_list:
                if dfw_section_name in val:
                    # Section with the same name already exist
                    #dfw_section_id = str(val[1])
                    #response = dfw_section_update(client_session, 
                    #              dfw_section_id, dfw_section_name, 
                    #              dfw_section_type, rules_schema)
                    #module.exit_json(changed=False, argument_spec=module.params)
                    module.fail_json(msg='Update of existing L3Redirect Section is not implemented yet.')
        response = dfw_section_create(client_session, 
                        dfw_section_name, dfw_section_type, rules_schema)
        module.exit_json(changed=True, argument_spec=module.params, response=response)
    elif 'absent' in module.params['state']:
        if dfw_section_type == 'L2':
            for val in l2_section_list:
                if dfw_section_name in val and str(val[0]) != 'Default Section Layer2':
                    # Section already exists and is not default section
                    dfw_section_id = str(val[1])
                    response=dfw_section_delete(client_session, dfw_section_id, 'L2')
                    module.exit_json(changed=True, argument_spec=module.params, response=response)

        elif dfw_section_type == 'L3':
            for val in l3_section_list:
                if dfw_section_name in val and str(val[0]) != 'Default Section Layer3':
                    # Section already exists and is not default section
                    dfw_section_id = str(val[1])
                    response=dfw_section_delete(client_session, dfw_section_id, 'L3')
                    module.exit_json(changed=True, argument_spec=module.params, response=response)

        elif dfw_section_type == 'L3R':
            for val in l3r_section_list:
                if dfw_section_name in val and str(val[0]) != 'Default Section':
                    # Section already exists and is not default section
                    dfw_section_id = str(val[1])
                    response=dfw_section_delete(client_session, dfw_section_id, 'L3R')
                    module.exit_json(changed=True, argument_spec=module.params, response=response)

        module.exit_json(changed=False, argument_spec=module.params)

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *
from sys import path
path.append('library/')
from lib_dfw_utils import dfw_rule_parse, dfw_rule_construct, dfw_section_list, dfw_section_create, dfw_section_update, dfw_section_delete

if __name__ == '__main__':
    main()
