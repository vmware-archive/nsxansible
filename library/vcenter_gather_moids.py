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
import requests
import ssl



VIM_TYPES = {'datacenter': [vim.Datacenter],
             'dvs_name': [vim.dvs.VmwareDistributedVirtualSwitch],
             'datastore_name': [vim.Datastore],
             'resourcepool_name': [vim.ResourcePool]}


def get_cluster_mo(datacenter_mo, cluster_name):
    host_folder = datacenter_mo.hostFolder
    for child in host_folder.childEntity:
        if child.name == cluster_name:
            return child
    return None


def get_portgroup_mo(datacenter_mo, portgroup_name):
    network_folder = datacenter_mo.network
    for network in network_folder:
        if network.name == portgroup_name:
            return network
    return None


def get_mo(content, searchedname, vim_type_list):
    mo = get_all_objs(content, vim_type_list)
    for object in mo:
        if object.name == searchedname:
            return object
    return None


def get_all_objs(content, vimtype):
    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj


def connect_to_api(vchost, vc_user, vc_pwd):
    requests.packages.urllib3.disable_warnings()
    if hasattr(ssl, 'SSLContext'):
     context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
     context.verify_mode = ssl.CERT_NONE
    else:
        context = None
    if context:
        service_instance = SmartConnect(host=vchost, user=vc_user, pwd=vc_pwd, sslContext=context)
    else:
        service_instance = SmartConnect(host=vchost, user=vc_user, pwd=vc_pwd)


    return service_instance.RetrieveContent()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            datacenter_name=dict(required=True),
            cluster_name=dict(type='str'),
            resourcepool_name=dict(type='str'),
            dvs_name=dict(type='str'),
            portgroup_name=dict(type='str'),
            datastore_name=dict(type='str')
        ),
        required_one_of=[['cluster_name', 'portgroup_name', 'resourcepool_name', 'dvs_name', 'datastore_name']],
        mutually_exclusive=[['cluster_name', 'portgroup_name', 'resourcepool_name', 'dvs_name', 'datastore_name']],
        supports_check_mode=False
    )

    try:
        content = connect_to_api(module.params['hostname'], module.params['username'], module.params['password'])
    except vim.fault.InvalidLogin:
        module.fail_json(msg='exception while connecting to vCenter, login failure, check username and password')
    except requests.exceptions.ConnectionError:
        module.fail_json(msg='exception while connecting to vCenter, check hostname, FQDN or IP')

    searched_parameters = ['cluster_name', 'portgroup_name', 'resourcepool_name', 'dvs_name', 'datastore_name']

    datacenter_mo = get_mo(content, module.params['datacenter_name'], VIM_TYPES['datacenter'])
    datacenter_moid =  datacenter_mo._moId

    for searched_parameter in searched_parameters:
        if searched_parameter == 'cluster_name' and module.params[searched_parameter]:
            object_mo = get_cluster_mo(datacenter_mo, module.params[searched_parameter])
        elif searched_parameter == 'portgroup_name' and module.params[searched_parameter]:
            object_mo = get_portgroup_mo(datacenter_mo, module.params[searched_parameter])
        elif searched_parameter and module.params[searched_parameter]:
            object_mo = get_mo(content, module.params[searched_parameter], VIM_TYPES[searched_parameter])

    object_id = object_mo._moId

    module.exit_json(changed=False, object_id=object_id, datacenter_moid=datacenter_moid)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()

