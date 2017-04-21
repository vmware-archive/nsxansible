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

__author__ = 'ynakaoku'

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


VIM_TYPES = {'datacenter': [vim.Datacenter],
             'dvs_name': [vim.dvs.VmwareDistributedVirtualSwitch],
             'vm_name': [vim.VirtualMachine]}


def get_uuid(content, searchedname, vim_type_list, instance_uuid_flag):
    mo = get_all_objs(content, vim_type_list)
    for object in mo:
        if object.config.name == searchedname:
            if instance_uuid_flag:
                return object.config.instanceUuid
            else:
                return object.config.uuid
    return None

def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            datacenter_name=dict(required=True),
            dvs_name=dict(type='str'),
            vm_name=dict(type='str'),
            uuid_type=dict(type='str')
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['dvs_name', 'vm_name']],
        mutually_exclusive=[['dvs_name', 'vm_name']],
        supports_check_mode=False
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    content = connect_to_api(module)

    searched_parameters = ['dvs_name', 'vm_name']

    datacenter_mo = find_datacenter_by_name(content, module.params['datacenter_name'])
    datacenter_moid =  datacenter_mo._moId

    for searched_parameter in searched_parameters:
        if searched_parameter and module.params[searched_parameter]:
            if module.params['uuid_type'] == 'instance':
                uuid = get_uuid(content, module.params[searched_parameter], VIM_TYPES[searched_parameter], True)
            else:
                uuid = get_uuid(content, module.params[searched_parameter], VIM_TYPES[searched_parameter], False)

    module.exit_json(changed=False, uuid=uuid, datacenter_moid=datacenter_moid)

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()

