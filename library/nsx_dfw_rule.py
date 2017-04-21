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
            section=dict(required=True),
            disabled=dict(default='false', choice=['true', 'false']),
            src_any=dict(default='true', choice=['true', 'false']),
            src_excluded=dict(default='false', choice=['true', 'false']),
            sources=dict(default=[], type='list'),
            dest_any=dict(default='true', choice=['true', 'false']),
            dest_excluded=dict(default='false', choice=['true', 'false']),
            destinations=dict(default=[], type='list'),
            service_any=dict(default='true', choice=['true', 'false']),
            services=dict(default = [], type='list'),
            action=dict(default='allow', choice=['allow', 'deny', 'block', 'reject']),
            logged=dict(default='false', choice=['true', 'false']),
            direction=dict(default='inout', choice=['in', 'out', 'inout']),
            pkt_type=dict(default='any'),
            applyto=dict(default='dfw', choice=['any', 'dfw', 'edgegw'])
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
    result, dfw_params = dfw_rule_parse(client_session, module.params, l2_section_list, l3r_section_list, l3_section_list)
    if not result:
        module.fail_json(msg=dfw_params)

#    dfw_params = module.params
#    if dfw_params['src_any'] == 'true':
#        dfw_params['sources'] = ''
#    if dfw_params['dest_any'] == 'true':
#        dfw_params['destinations'] = ''
#    if dfw_params['service_any'] == 'true':
#        dfw_params['services']  = ''
#    dfw_params['note']  = ''
#    dfw_params['tag']  = ''
#
#    l2_section_list, l3r_section_list, l3_section_list, detailed_dfw_sections = dfw_section_list(client_session)
#
#    # check section type and existence of rule.
#    for val in l2_section_list:
#        if dfw_params['section'] in val:
#            # Section with the same name already exist
#            dfw_params['section_type'] = 'L2'
#            dfw_params['section_id'] = str(val[1])
#            dfw_rule_id_dict = dfw_rule_id_read(client_session, dfw_params['section_id'], dfw_params['name'])
#            if len(dfw_rule_id_dict) == 0:
#                dfw_params['rule_id'] = None
#                break
#            elif len(dfw_rule_id_dict) == 1 and len(dfw_rule_id_dict[dfw_params['name']]) == 1:
#                dfw_params['rule_id'] = str(dfw_rule_id_dict[dfw_params['name']][0])
#                break
#            else:
#                module.fail_json(msg='Overlapped rule name exists in one section: L2.')
#    else:
#        for val in l3_section_list:
#            if dfw_params['section'] in val:
#                # Section with the same name already exist
#                dfw_params['section_type'] = 'L3'
#                dfw_params['section_id'] = str(val[1])
#                dfw_rule_id_dict = dfw_rule_id_read(client_session, dfw_params['section_id'], dfw_params['name'])
#                if len(dfw_rule_id_dict) == 0:
#                    dfw_params['rule_id'] = None
#                    break
#                elif len(dfw_rule_id_dict) == 1 and len(dfw_rule_id_dict[dfw_params['name']]) == 1:
#                    dfw_params['rule_id'] = str(dfw_rule_id_dict[dfw_params['name']][0])
#                    break
#                else:
#                    module.fail_json(msg='Overlapped rule name exists in one section: L3.')
#        else: 
#            for val in l3r_section_list:
#                if dfw_params['section'] in val:
#                    # Section with the same name already exist
#                    dfw_params['section_type'] = 'L3R'
#                    dfw_params['section_id'] = str(val[1])
#                    dfw_rule_id_dict = dfw_rule_id_read(client_session, dfw_params['section_id'], dfw_params['name'])
#                    if len(dfw_rule_id_dict) == 0:
#                        dfw_params['rule_id'] = None
#                        break
#                    elif len(dfw_rule_id_dict) == 1 and len(dfw_rule_id_dict[dfw_params['name']]) == 1:
#                        dfw_params['rule_id'] = dfw_rule_id_dict[dfw_params['name']][0]
#                        break
#                    else:
#                        module.fail_json(msg='Overlapped rule name exists in one section: L3R.')
#            else:
#                if module.params['state'] == 'absent':
#                    module.exit_json(changed=False, argument_spec=module.params)
#                else:
#                    module.fail_json(msg='section does not exist.')

    if 'present' in module.params['state']:

#        if dfw_params['section_type'] == 'L2':
#            # If DFW section is Layer2
#            if dfw_params['pkt_type'] != 'any':
#                module.fail_json(msg='For a L2 rule "any" is the only allowed value for parameter -pktype')
#            if dfw_params['action'] != 'allow' and dfw_params['action'] != 'block':
#                module.fail_json(msg='For a L2 rule "allow/block" are the only allowed value for parameter -action')
#            if dfw_params['applyto'] == 'any' or dfw_params['applyto'] == 'edgegw':
#                module.fail_json(msg='For a L2 rule "any" and "edgegw" are not allowed values for parameter applyto')
#            if dfw_params['src_any'] == 'false':
#              for item in dfw_params['sources']:
#                if item['type'] == 'ipset':
#                  module.fail_json(msg='For a L2 rule "ipset" is not an allowed value as source')
#            if dfw_params['dest_any'] == 'false':
#              for item in dfw_params['destinations']:
#                if item['type'] == 'ipset':
#                  module.fail_json(msg='For a L2 rule "ipset" is not an allowed value as destination')
#            if dfw_params['action'] == 'block':
#                dfw_params['action'] = 'deny'
#
#        elif dfw_params['section_type'] == 'L3':
#            # If DFW section is Layer3
#            if dfw_params['action'] == 'block':
#                dfw_params['action'] = 'deny'
#
#        else:
#            # If DFW section is Layer3 Redirection
#            module.fail_json(msg='Error: L3 redirect rules are not supported in this version. Aborting. No action have been performed on the system') 

        vccontent = connect_to_api(module)

        rule_schema = dfw_rule_construct(client_session, dfw_params, vccontent)

        if dfw_params['rule_id'] == None:
            # DFW rule must be newly created.
            result, response = dfw_rule_create(client_session, 
                                         dfw_params['section_id'], 
                                         dfw_params['section_type'], 
                                         rule_schema)

            if not result:
                module.fail_json(msg='rule creation method was halted with message: {}.'.format(response))

            module.exit_json(changed=True, argument_spec=module.params, response=response)

        elif dfw_params['rule_id'] != None:
            # DFW rule must be updated.
            result, response = dfw_rule_update(client_session, 
                                         dfw_params['section_id'], 
                                         dfw_params['section_type'], 
                                         dfw_params['rule_id'], 
                                         rule_schema)

            if not result:
                module.fail_json(msg='rule update method was halted with message: {}.'.format(response))

            module.exit_json(changed=True, argument_spec=module.params, response=response)

    elif 'absent' in module.params['state']:
        if dfw_params['rule_id'] != None:
            if not dfw_params['section'] in ['Default Section Layer2','Default Section Layer3','Default Section']:
                # Section is not default section
                result, response = dfw_rule_delete(client_session,
                                         dfw_params['section_id'], 
                                         dfw_params['section_type'], 
                                         dfw_params['rule_id'])
                if not result:
                    module.fail_json(msg='DFW rule deletion failed for {}.'.format(response))
                module.exit_json(changed=True, argument_spec=module.params, response=response)
            else:
                module.fail_json(msg='DFW rule deletion was rejected as it belongs to Default Rule Section.')
        else:
            module.fail_json(msg='DFW rule id is not found.')

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *
#from pynsxv.library.libutils import nametovalue, dfw_rule_list_helper, get_ipsets, get_macsets, get_secgroups
from sys import path
path.append('library/')
from lib_dfw_utils import dfw_section_list, dfw_rule_id_read, dfw_rule_parse, dfw_rule_construct, dfw_rule_create, dfw_rule_update, dfw_rule_delete

if __name__ == '__main__':
    main()
