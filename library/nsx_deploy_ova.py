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


import requests


def check_nsx_api(module):
    appliance_check_url = 'https://{}//api/2.0/services/vcconfig'.format(module.params['ip_address'])
    try:
        response = requests.request('GET', appliance_check_url,
                                    auth=('admin', module.params['admin_password']), verify=False)
    except requests.exceptions.ConnectionError:
        return False

    return response.status_code, response.content


def wait_for_api(module, sleep_time=15):
    status_poll_count = 0
    while status_poll_count < 30:
        api_status = check_nsx_api(module)
        if api_status:
            if api_status[0] == 200:
                return True
            else:
                status_poll_count += 1
                time.sleep(sleep_time)
        else:
            status_poll_count += 1
            time.sleep(sleep_time)

        if status_poll_count == 30:
            return False


def find_virtual_machine(content, searched_vm_name):
    virtual_machines = get_all_objs(content, [vim.VirtualMachine])
    for vm in virtual_machines:
        if vm.name == searched_vm_name:
            return vm
    return None



def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            ovftool_path=dict(required=True, type='str'),
            datacenter=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            portgroup=dict(required=True, type='str'),
            cluster=dict(required=True, type='str'),
            vmname=dict(required=True, type='str'),
            nsxhostname=dict(required=True, type='str'),
            dns_server=dict(required=True, type='str'),
            ntp_server=dict(required=True, type='str'),
            dns_domain=dict(required=True, type='str'),
            gateway=dict(required=True, type='str'),
            ip_address=dict(required=True, type='str'),
            netmask=dict(required=True, type='str'),
            admin_password=dict(required=True, type='str', no_log=True),
            enable_password=dict(required=True, type='str', no_log=True),
            path_to_ova=dict(required=True, type='str'),
            ova_file=dict(required=True, type='str'),
            disk_mode=dict(default='thin'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    content = connect_to_api(module)

    nsx_manager_vm = find_virtual_machine(content, module.params['vmname'])

    if nsx_manager_vm:
        api_status = check_nsx_api(module)
        if not api_status:
            module.fail_json(msg='A VM with the name {} was already present, but the '
                                 'API did not respond'.format(module.params['vmname']))
        elif api_status[0] != 200:
            module.fail_json(msg='NSX Manager returned an error code, the response '
                                 'was {} {}'.format(api_status[0], api_status[1]))
        else:
            module.exit_json(changed=False, nsx_manager_vm=str(nsx_manager_vm))

    if module.check_mode:
        module.exit_json(changed=True)

    ovftool_exec = '{}/ovftool'.format(module.params['ovftool_path'])
    ova_file = '{}/{}'.format(module.params['path_to_ova'], module.params['ova_file'])
    vi_string = 'vi://{}:{}@{}/{}/host/{}/'.format(module.params['username'],
                                                   module.params['password'], module.params['hostname'],
                                                   module.params['datacenter'], module.params['cluster'])

    ova_tool_result = module.run_command([ovftool_exec,
                                          '--acceptAllEulas',
                                          '--skipManifestCheck',
                                          '--powerOn',
                                          '--noSSLVerify',
                                          '--allowExtraConfig',
                                          '--diskMode={}'.format(module.params['disk_mode']),
                                          '--datastore={}'.format(module.params['datastore']),
                                          '--net:VSMgmt={}'.format(module.params['portgroup']),
                                          '--name={}'.format(module.params['vmname']),
                                          '--prop:vsm_hostname={}'.format(module.params['nsxhostname']),
                                          '--prop:vsm_isSSHEnabled={}'.format(True),
                                          '--prop:vsm_dns1_0={}'.format(module.params['dns_server']),
                                          '--prop:vsm_domain_0={}'.format(module.params['dns_domain']),
                                          '--prop:vsm_ntp_0={}'.format(module.params['ntp_server']),
                                          '--prop:vsm_gateway_0={}'.format(module.params['gateway']),
                                          '--prop:vsm_ip_0={}'.format(module.params['ip_address']),
                                          '--prop:vsm_netmask_0={}'.format(module.params['netmask']),
                                          '--prop:vsm_cli_passwd_0={}'.format(module.params['admin_password']),
                                          '--prop:vsm_cli_en_passwd_0={}'.format(module.params['enable_password']),
                                          ova_file,
                                          vi_string])

    if ova_tool_result[0] != 0:
        module.fail_json(msg='Failed to deploy OVA, error message from ovftool is: {}'.format(ova_tool_result[1]))
    if not wait_for_api(module):
        module.fail_json(msg='Failed to deploy OVA, timed out waiting for the API to become available')

    module.exit_json(changed=True, ova_tool_result=ova_tool_result)

from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()
