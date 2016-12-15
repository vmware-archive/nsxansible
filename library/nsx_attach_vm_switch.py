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

def get_logical_switch(client_session, logical_switch_name):
    """
    :param client_session: An instance of an NsxClient Session
    :param logical_switch_name: The name of the logical switch searched
    :return: A tuple, with the first item being the logical switch id as string of the first Scope found with the
             right name and the second item being a dictionary of the logical parameters as return by the NSX API
    """
    all_lswitches = client_session.read_all_pages('logicalSwitchesGlobal', 'read')
    try:
        logical_switch_params = [scope for scope in all_lswitches if scope['name'] == logical_switch_name][0]
        logical_switch_id = logical_switch_params['objectId']
    except IndexError:
        return None

    return logical_switch_id

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            nsxmanager_spec=dict(required=True, no_log=True, type='dict'),
            portgroup_id=dict(default=None),
            logicalswitch=dict(default=None),
            objectUUID=dict(required=True),
        ),
        supports_check_mode=False
    )

    portgroup_id = module.params['portgroup_id']
    logicalswitch = module.params['logicalswitch']
    
    if portgroup_id != None and logicalswitch != None:
      module.fail_json(msg='Only et portgroup_id OR logicalswitch, not both!')

    from nsxramlclient.client import NsxClient
    client_session = NsxClient(module.params['nsxmanager_spec']['raml_file'], module.params['nsxmanager_spec']['host'],
                             module.params['nsxmanager_spec']['user'], module.params['nsxmanager_spec']['password'])

    if logicalswitch != None:
      lswitch_id = get_logical_switch(client_session, logicalswitch)
      portgroup_id = lswitch_id

    changed=False

    if module.params['state'] == 'absent':
      if portgroup_id != None:
       module.fail_json(msg='If VM must be detached, don\'t set portgroup or logicalswitch') 
    
    action = attachVmToPortgroup(client_session, module.params['objectUUID'],  portgroup_id)

    if action:
      changed=True
    module.exit_json(changed=changed)

def attachVmToPortgroup(client_session, objectUUID, portgroup_id):
  attach = { 'com.vmware.vshield.vsm.inventory.dto.VnicDto': 
      { 
        'objectId': objectUUID + '.000', 'vnicUuid': objectUUID + '.000', 
        'portgroupId': portgroup_id } 
    }
  return client_session.create('logicalSwitchVmAttach', request_body_dict=attach)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
