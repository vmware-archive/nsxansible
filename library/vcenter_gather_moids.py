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

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


VIM_TYPES = {'datacenter': [vim.Datacenter],
             'dvs_name': [vim.dvs.VmwareDistributedVirtualSwitch],
             'datastore_name': [vim.Datastore],
             'resourcepool_name': [vim.ResourcePool],
             'portgroup_name': [vim.dvs.DistributedVirtualPortgroup, vim.Network]}


def get_mo(content, searchedname, vim_type_list):
    mo = get_all_objs(content, vim_type_list)
    for object in mo:
        if object.name == searchedname:
            return object
	elif re.search( searchedname, object.name ):
            return object
    return None

def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            datacenter_name=dict(required=True),
            cluster_name=dict(type='str'),
            resourcepool_name=dict(type='str'),
            dvs_name=dict(type='str'),
            portgroup_name=dict(type='str'),
            datastore_name=dict(type='str')
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['cluster_name', 'portgroup_name', 'resourcepool_name', 'dvs_name', 'datastore_name']],
        mutually_exclusive=[['cluster_name', 'portgroup_name', 'resourcepool_name', 'dvs_name', 'datastore_name']],
        supports_check_mode=False
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    content = connect_to_api(module)

    searched_parameters = ['cluster_name', 'portgroup_name', 'resourcepool_name', 'dvs_name', 'datastore_name']

    datacenter_mo = find_datacenter_by_name(content, module.params['datacenter_name'])
    datacenter_moid =  datacenter_mo._moId

    object_mo = None

    for searched_parameter in searched_parameters:
        if searched_parameter == 'cluster_name' and module.params[searched_parameter]:
            object_mo = find_cluster_by_name_datacenter(datacenter_mo, module.params[searched_parameter])
        elif searched_parameter and module.params[searched_parameter]:
            object_mo = get_mo(content, module.params[searched_parameter], VIM_TYPES[searched_parameter])

        if not object_mo and module.params[searched_parameter]:
            module.fail_json(msg='Could not find {} in vCenter'.format(module.params[searched_parameter]))

    object_id = object_mo._moId
    object_name = object_mo.name

    module.exit_json(changed=False, object_id=object_id, object_name=object_name, datacenter_moid=datacenter_moid)

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()

