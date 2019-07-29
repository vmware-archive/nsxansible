#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2018 VMware, Inc. All Rights Reserved.
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

__author__ = 'virtualelephant'

try:
    from pyVmomi import vim, vmodl
    from pyVmomi.connect import SmartConnect
    HAS_PYVMOMI = True

except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import *

def get_user_role(client_session, user_id):
    """
    :param client_session: An instance of an NsxClient session
    :param user_id: The userId. To specify a domain user, use user@domain not domain\user
    """

    cfg_result = client_session.read('userRoleMgmt', uri_parameters={'userId': user_id})

    if cfg_result['status'] == 200:
        return cfg_result

    return False

def update_user_role(client_session, user_id, role_type):
    """
    :param client_session: An instance of an NsxClient session
    :param user_id: The userId. To specify a domain user, use user@domain not domain\user
    :param role_type: Users assigned role. Possible roles are super_user, vshield_admin, enterprise_admin, security_admin, auditor
    """

    role_body_dict = { 'role': role_type }

    cfg_result = client_session.update('userRoleMgmt', uri_parameters={'userId': user_id},
                                                       request_body_dict={'accessControlEntry': role_body_dict})

    if cfg_result['status'] == 200:
        return True
    else:
        return False

def create_user_role(client_session, user_id, role_type, is_group):
    """
    :param client_session: An instance of an NsxClient session
    :param user_id: The userId. To specify a domain user, use user@domain not domain\user
    :param role_type: Users assigned role. Possible roles are super_user, vshield_admin, enterprise_admin, security_admin, auditor
    :param is_group: Query parameter. True to apply to a group, false to apply to a user. Default is false.
    """

    role_body_dict = { 'role': role_type }

    cfg_result = client_session.create('userRoleMgmt', uri_parameters={'userId': user_id},
                                                       request_body_dict={'accessControlEntry': role_body_dict},
                                                       query_parameters_dict={'isGroup': is_group})

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def delete_user_role(client_session, user_id):
    """
    :param client_session: An instance of an NsxClient session
    :param user_id: The userID. To specify a domain user, use user@domain not domain\user
    """

    cfg_result = client_session.delete('userRoleMgmt', uri_parameters={'userId': user_id})

    if cfg_result['status'] == 204:
        return True
    else:
        return False

def main():
    module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='present', choices=['present', 'update', 'absent']),
                nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
                name=dict(required=True),
                is_group=dict(default='false', choices=['true', 'false']),
                role_type=dict(choices=['super_user', 'vshield_admin', 'security_admin', 'auditor', 'enterprise_admin'])
            ),
            supports_check_mode=False
    )

    from nsxramlclient.client import NsxClient

    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'],
                               module.params['nsxmanager_spec']['host'],
                               module.params['nsxmanager_spec']['user'],
                               module.params['nsxmanager_spec']['password'],
                               fail_mode="continue")

    changed = False

    user_role = get_user_role(client_session, module.params['name'])

    if user_role:
        if module.params['state'] == 'present':
            if module.params['role_type'] != user_role['body']['accessControlEntry']['role']:
                changed = update_user_role(client_session, module.params['name'], module.params['role_type'])
        elif module.params['state'] == 'update':
            changed = update_user_role(client_session, module.params['name'], module.params['role_type'])        
        elif module.params['state'] == 'absent':
            changed = delete_user_role(client_session, module.params['name'])
    else:
        if module.params['state'] == 'present':
            changed = create_user_role(client_session, module.params['name'], module.params['role_type'], module.params['is_group'])
        elif module.params['state'] == 'update':
            changed = create_user_role(client_session, module.params['name'], module.params['role_type'], module.params['is_group'])

    module.exit_json(changed=changed)
    #if changed:
    #    module.exit_json(changed=True)
    #else:
    #    module.exit_json(changed=False)

if __name__ == '__main__':
    main()
