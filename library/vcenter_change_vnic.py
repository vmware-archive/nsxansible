#!/usr/bin/env python
# coding=utf-8
#
# Copyright c 2015 VMware, Inc. All Rights Reserved.
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
#
# VMware vSphere Python SDK
# Copyright (c) 2008-2013 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'ynakaoku'

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

#from tools import tasks
from pyVim import connect
#from pyVim.connect import SmartConnect, Disconnect
import re

#import atexit
#import argparse
#import getpass
#import ssl

def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def search_obj(content, vimtype, name):
    obj = []
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if re.search(name, c.name):
            obj.append(c)
#            break
    return obj

#def change_nic(si, vm, network):
def change_nic(vm, network):
    """
    :param si: Service Instance
    :param vm: Virtual Machine Object
    :param network: Virtual Network
    """
    spec = vim.vm.ConfigSpec()
    nic_changes = []

    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.edit
            nic_spec.device = device
            nic_spec.device.wakeOnLanEnabled = True

            dvs_port_connection = vim.dvs.PortConnection()
            dvs_port_connection.portgroupKey = network.key
            dvs_port_connection.switchUuid = \
                network.config.distributedVirtualSwitch.uuid
            nic_spec.device.backing = \
                vim.vm.device.VirtualEthernetCard. \
                DistributedVirtualPortBackingInfo()
            nic_spec.device.backing.port = dvs_port_connection

            nic_spec.device.connectable = \
                vim.vm.device.VirtualDevice.ConnectInfo()
            nic_spec.device.connectable.startConnected = True
            nic_spec.device.connectable.allowGuestControl = True
            nic_spec.device.connectable.connected = True
            nic_changes.append(nic_spec)
            break

#    nic_spec = vim.vm.device.VirtualDeviceSpec()
#    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

#    nic_spec.device = vim.vm.device.VirtualE1000()

#    nic_spec.device.deviceInfo = vim.Description()
#    nic_spec.device.deviceInfo.summary = 'vCenter API test'

#    nic_spec.device.backing = \
#        vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
#    nic_spec.device.backing.useAutoDetect = False
#    content = si.RetrieveContent()
#    nic_spec.device.backing.network = get_obj(content, [vim.Network], network)
#    nic_spec.device.backing.deviceName = network
#    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
#    nic_spec.device.connectable.startConnected = True
#    nic_spec.device.connectable.startConnected = True
#    nic_spec.device.connectable.allowGuestControl = True
#    nic_spec.device.connectable.connected = False
#    nic_spec.device.connectable.status = 'untried'
#    nic_spec.device.wakeOnLanEnabled = True
#    nic_spec.device.addressType = 'assigned'

    config_spec = vim.vm.ConfigSpec(deviceChange=nic_changes)
    wait_for_task(vm.ReconfigVM_Task(config_spec))
#    task = vm.ReconfigVM_Task(config_spec)
#    tasks.wait_for_tasks(si, [task])
#    print "Successfully changed network: " + network.name

#    nic_changes.append(nic_spec)
#    spec.deviceChange = nic_changes
#    e = vm.ReconfigVM_Task(spec=spec)
#    print "NIC CARD ADDED"

def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            vm_name=dict(required=True, type='str'),
            network=dict(required=True, type='str')
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    content = connect_to_api(module)

    vm = get_obj(content, [vim.VirtualMachine], module.params['vm_name'])
    networks = search_obj(content,
                 [vim.dvs.DistributedVirtualPortgroup], 
                 module.params['network'])

    if len(networks) > 1:
      module.fail_json(msg='multiple candidate networks are found, exit')
    if len(networks) < 1:
      module.fail_json(msg='no network interface is found, exit')

    network = networks[0]

    for connected in vm.network:
      if connected == network:
        module.exit_json(change=False)
     
    if vm:
#          change_nic(service_instance, vm, networks[0])
      change_nic(vm, networks[0])
    else:
      module.fail_json(msg='target vm is not found, exit')

    module.exit_json(changed=True)

# Start program
from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == "__main__":
    main()
