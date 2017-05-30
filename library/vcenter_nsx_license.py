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

__author__ = 'yasensim'

import requests, ssl

try:
    from pyVmomi import vim, vmodl
    from pyVim.connect import SmartConnect
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

def connect_to_api(vchost, vc_user, vc_pwd):
    global service_instance
    try:
        service_instance = SmartConnect(host=vchost, user=vc_user, pwd=vc_pwd)
    except (requests.ConnectionError, ssl.SSLError):
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            service_instance = SmartConnect(host=vchost, user=vc_user, pwd=vc_pwd, sslContext=context)
        except Exception as e:
            raise Exception(e)
    return service_instance.RetrieveContent()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            vcenter=dict(required=True, type='str'),
            vcenter_user=dict(required=True, type='str'),
            vcenter_passwd=dict(required=True, type='str', no_log=True),
	    license_key=dict(required=True, type='str', no_log=True)
        ),
        supports_check_mode=False
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    try:
        content = connect_to_api(module.params['vcenter'], module.params['vcenter_user'],
                                 module.params['vcenter_passwd'])
    except vim.fault.InvalidLogin:
        module.fail_json(msg='exception while connecting to vCenter, login failure, check username and password')
    except requests.exceptions.ConnectionError:
        module.fail_json(msg='exception while connecting to vCenter, check hostname, FQDN or IP')
    lm = content.licenseManager
    lam = lm.licenseAssignmentManager
    lam.UpdateAssignedLicense("nsx-netsec", module.params['license_key'], "NSX for vSphere")
    module.exit_json(changed=True, result="NSX License Applied!!!")

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()

