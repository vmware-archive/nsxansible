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


from pyVim.connect import SmartConnect
from pyVmomi import vim, vmodl


VIM_TYPES = {'datacenter': [vim.Datacenter],
             'dvs': [vim.dvs.VmwareDistributedVirtualSwitch],
             'datastore': [vim.Datastore],
             'resourcepool': [vim.ResourcePool]}


def get_cluster_mo(datacenter_mo, name):
    host_folder = datacenter_mo.hostFolder
    for child in host_folder.childEntity:
        if child.name == name:
            return child
    return None


def get_portgroup_mo(datacenter_mo, name):
    network_folder = datacenter_mo.network
    for network in network_folder:
        if network.name == name:
            return network
    return None


def get_mo(content, searchedname, vim_type_list):
    mo = get_all_objs(content, vim_type_list)
    for object in mo:
        if object.name == searchedname:
            return object
    return None


def get_moid_dict(content, vim_type, name_list):
    result_dict = {}
    for name in name_list:
        result_dict.update({name: get_mo(content, name, vim_type)._moId})
    return result_dict


def get_all_objs(content, vimtype):
    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj


def connect_to_api(vchost, user, pwd):
    service_instance = SmartConnect(host=vchost, user=user, pwd=pwd)
    return service_instance.RetrieveContent()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            datacenter_name=dict(required=True),
            cluster_names=dict(type='list'),
            resourcepool_names=dict(type='list'),
            dvs_names=dict(type='list'),
            portgroup_names=dict(type='list'),
            datastore_names=dict(type='list')
        ),
        supports_check_mode=False
    )

    try:
        content = connect_to_api(module.params['hostname'], module.params['username'], module.params['password'])
    except:
        module.fail_json(msg='exception while connecting to vCenter, check paramters like hostname, username and pwd')

    vcenter_moids = {}

    datacenter_mo = get_mo(content, module.params['datacenter_name'], VIM_TYPES['datacenter'])
    vcenter_moids.update({'datacenter': datacenter_mo._moId})

    if module.params['cluster_names']:
        vcenter_moids.update({'cluster_names': {}})
        for cluster_name in module.params['cluster_names']:
            cluster_mo = get_cluster_mo(datacenter_mo, cluster_name)
            vcenter_moids['cluster_names'].update({cluster_name: cluster_mo._moId})

    if module.params['portgroup_names']:
        vcenter_moids.update({'portgroup_names': {}})
        for portgroup_name in module.params['portgroup_names']:
            portgroup_mo = get_portgroup_mo(datacenter_mo, portgroup_name)
            vcenter_moids['portgroup_names'].update({portgroup_name: portgroup_mo._moId})

    if module.params['resourcepool_names']:
        vcenter_moids.update({'resourcepool_names': get_moid_dict(content,
                                                VIM_TYPES['resourcepool'],
                                                module.params['resourcepool_names'])})

    if module.params['dvs_names']:
        vcenter_moids.update({'dvs_names': get_moid_dict(content,
                                                VIM_TYPES['dvs'],
                                                module.params['dvs_names'])})

    if module.params['datastore_names']:
        vcenter_moids.update({'datastore_names': get_moid_dict(content,
                                                VIM_TYPES['datastore'],
                                                module.params['datastore_names'])})


    module.exit_json(changed=False, moids=vcenter_moids)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()